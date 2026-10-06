import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"

/*
 * Engine Requirement - what liquid rocket engine is wanted (LIQ-2).
 *
 * Intent, not a calculation. The page records a target thrust in a design
 * environment, a burn time, and the designer's preferences about the
 * propellant pair, chamber pressure, O/F, feed architecture and power cycle.
 * There is no Calculate button because there is nothing to calculate: editing
 * a field replaces the controller's requirement and solves nothing.
 *
 * Every option list, label, unit and issue comes from the EngineRequirement
 * controller. This file only lays them out.
 *
 *   - "Auto" leaves a decision open. It is listed under Open decisions, never
 *     resolved here.
 *   - Feed architecture and power cycle are separate controls. The cycle is
 *     only offered for a pump-fed engine; a pressure-fed engine has none.
 *   - The propellant pair is chosen from the liquid propellant catalogue by
 *     key; withheld catalogue pairs are named with their reason.
 */
Item {
    id: page

    function indexOfKey(options, key) {
        for (var i = 0; i < options.length; ++i)
            if (options[i].key === key)
                return i
        return -1
    }

    function labels(options) {
        return options.map(function (o) { return o.label })
    }

    function issueFor(field) {
        var issues = EngineRequirement.issues
        for (var i = 0; i < issues.length; ++i)
            if (issues[i].field === field)
                return issues[i].message
        return ""
    }

    readonly property var pairChoices:
        [{ key: "", label: "Auto · pair left open" }].concat(EngineRequirement.pairOptions)

    component FieldNote: Text {
        Layout.fillWidth: true
        visible: text !== ""
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.meta
        wrapMode: Text.WordWrap
    }

    component IssueNote: Text {
        Layout.fillWidth: true
        visible: text !== ""
        color: Theme.warning
        font.family: Typography.sans
        font.pixelSize: Typography.meta
        wrapMode: Text.WordWrap
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.pagePadding
        spacing: Metrics.spacing.l

        RFPageHeader {
            Layout.fillWidth: true
            title: "Engine Requirement"
            subtitle: "Target, environment and design intent for a liquid rocket engine"

            trailing: Component {
                Row {
                    spacing: Metrics.spacing.s
                    RFStatusChip {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "Design intent · nothing solved"
                        showDot: false
                    }
                    RFStatusChip {
                        objectName: "requirementStatus"
                        anchors.verticalCenter: parent.verticalCenter
                        text: EngineRequirement.statusLabel
                        tone: EngineRequirement.isComplete ? "success" : "warning"
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Metrics.spacing.m

            // ---- the form ------------------------------------------------
            Flickable {
                id: formScroll
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentWidth: width
                contentHeight: form.implicitHeight
                boundsBehavior: Flickable.StopAtBounds
                clip: true
                ScrollBar.vertical: RFScrollBar {}

                ColumnLayout {
                    id: form
                    width: formScroll.width - Metrics.spacing.m
                    spacing: Metrics.spacing.m

                    RFPanel {
                        Layout.fillWidth: true
                        title: "Requirement"

                        RFTextField {
                            objectName: "requirementName"
                            Layout.fillWidth: true
                            label: "Name"
                            placeholder: "Untitled requirement"
                            text: EngineRequirement.name
                            onEdited: EngineRequirement.setName(text)
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.spacing.l

                            ColumnLayout {
                                Layout.fillWidth: false
                                Layout.preferredWidth: 220
                                Layout.alignment: Qt.AlignTop
                                RFNumberField {
                                    objectName: "requirementThrust"
                                    Layout.fillWidth: true
                                    label: "Target thrust"
                                    unit: EngineRequirement.units.thrust
                                    step: 1
                                    text: EngineRequirement.thrustText
                                    onEdited: EngineRequirement.setThrust(text)
                                }
                                IssueNote { text: page.issueFor("thrust") }
                            }

                            ColumnLayout {
                                Layout.fillWidth: false
                                Layout.preferredWidth: 180
                                Layout.alignment: Qt.AlignTop
                                RFNumberField {
                                    objectName: "requirementBurnTime"
                                    Layout.fillWidth: true
                                    label: "Burn time"
                                    unit: EngineRequirement.units.burn_time
                                    step: 1
                                    text: EngineRequirement.burnTimeText
                                    onEdited: EngineRequirement.setBurnTime(text)
                                }
                                IssueNote { text: page.issueFor("burn_time") }
                            }
                            Item { Layout.fillWidth: true }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.spacing.l

                            RFComboBox {
                                objectName: "requirementAmbientMode"
                                Layout.preferredWidth: 240
                                Layout.alignment: Qt.AlignTop
                                label: "Design environment"
                                model: page.labels(EngineRequirement.ambientOptions)
                                currentIndex: page.indexOfKey(EngineRequirement.ambientOptions,
                                                              EngineRequirement.ambientMode)
                                onActivated: function (index) {
                                    EngineRequirement.setAmbientMode(
                                        EngineRequirement.ambientOptions[index].key)
                                }
                            }
                            ColumnLayout {
                                Layout.fillWidth: false
                                Layout.preferredWidth: 200
                                Layout.alignment: Qt.AlignTop
                                RFNumberField {
                                    objectName: "requirementAmbientPressure"
                                    Layout.fillWidth: true
                                    label: "Ambient pressure"
                                    unit: EngineRequirement.units.ambient_pressure
                                    step: 1
                                    readOnly: EngineRequirement.ambientMode !== "custom"
                                    text: EngineRequirement.ambientPressureText
                                    onEdited: EngineRequirement.setAmbientPressure(text)
                                }
                                IssueNote { text: page.issueFor("environment") }
                            }
                            Item { Layout.fillWidth: true }
                        }
                        FieldNote {
                            text: EngineRequirement.ambientOptions[
                                      Math.max(0, page.indexOfKey(EngineRequirement.ambientOptions,
                                                                  EngineRequirement.ambientMode))].note
                        }
                    }

                    RFPanel {
                        Layout.fillWidth: true
                        title: "Propellant and chamber"

                        RFComboBox {
                            objectName: "requirementPair"
                            Layout.preferredWidth: 420
                            label: "Propellant pair"
                            model: page.labels(page.pairChoices)
                            currentIndex: Math.max(0, page.indexOfKey(page.pairChoices,
                                                                      EngineRequirement.pairKey))
                            onActivated: function (index) {
                                EngineRequirement.setPair(page.pairChoices[index].key)
                            }
                        }
                        IssueNote { text: page.issueFor("propellant") }
                        FieldNote {
                            text: EngineRequirement.pairNote

                            HoverHandler { id: pairNoteHover }
                            RFTooltip {
                                visible: pairNoteHover.hovered
                                         && EngineRequirement.blockedPairs.length > 0
                                text: EngineRequirement.blockedPairs.length > 0
                                      ? EngineRequirement.blockedPairs[0].blocker : ""
                            }
                        }

                        RFSectionLabel { text: "Chamber pressure" }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.spacing.l
                            RFSegmentedControl {
                                objectName: "requirementChamberMode"
                                Layout.preferredWidth: 330
                                Layout.alignment: Qt.AlignVCenter
                                model: page.labels(EngineRequirement.chamberPressureOptions)
                                currentIndex: page.indexOfKey(EngineRequirement.chamberPressureOptions,
                                                              EngineRequirement.chamberPressureMode)
                                onSelected: function (index) {
                                    EngineRequirement.setChamberPressureMode(
                                        EngineRequirement.chamberPressureOptions[index].key)
                                }
                            }
                            RFNumberField {
                                objectName: "requirementChamberPressure"
                                Layout.preferredWidth: 180
                                visible: EngineRequirement.chamberPressureMode !== "auto"
                                label: "Chamber pressure"
                                unit: EngineRequirement.units.chamber_pressure
                                step: 0.1
                                text: EngineRequirement.chamberPressureText
                                onEdited: EngineRequirement.setChamberPressure(text)
                            }
                            Item { Layout.fillWidth: true }
                        }
                        IssueNote { text: page.issueFor("chamber_pressure") }

                        RFSectionLabel { text: "O/F" }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.spacing.l
                            RFSegmentedControl {
                                objectName: "requirementRatioMode"
                                Layout.preferredWidth: 360
                                Layout.alignment: Qt.AlignVCenter
                                model: page.labels(EngineRequirement.mixtureRatioOptions)
                                currentIndex: page.indexOfKey(EngineRequirement.mixtureRatioOptions,
                                                              EngineRequirement.mixtureRatioMode)
                                disabledIndices: EngineRequirement.pairKey === "" ? [1] : []
                                disabledNote: "Choose a propellant pair to use its reference O/F"
                                onSelected: function (index) {
                                    EngineRequirement.setMixtureRatioMode(
                                        EngineRequirement.mixtureRatioOptions[index].key)
                                }
                            }
                            RFNumberField {
                                objectName: "requirementRatio"
                                Layout.preferredWidth: 140
                                visible: EngineRequirement.mixtureRatioMode === "explicit"
                                label: "O/F (mass)"
                                step: 0.1
                                text: EngineRequirement.mixtureRatioText
                                onEdited: EngineRequirement.setMixtureRatio(text)
                            }
                            Text {
                                objectName: "requirementReferenceRatio"
                                visible: EngineRequirement.mixtureRatioMode === "pair_reference"
                                         && EngineRequirement.referenceMixtureRatioText !== ""
                                text: "O/F " + EngineRequirement.referenceMixtureRatioText
                                      + " · from the catalogue"
                                color: Theme.text
                                font.family: Typography.mono
                                font.pixelSize: Typography.body
                            }
                            Item { Layout.fillWidth: true }
                        }
                        IssueNote { text: page.issueFor("mixture_ratio") }
                    }

                    RFPanel {
                        Layout.fillWidth: true
                        title: "Feed and cycle"

                        RFSectionLabel { text: "Feed architecture" }
                        RFSegmentedControl {
                            objectName: "requirementFeed"
                            Layout.preferredWidth: 360
                            model: page.labels(EngineRequirement.feedOptions)
                            currentIndex: page.indexOfKey(EngineRequirement.feedOptions,
                                                          EngineRequirement.feed)
                            onSelected: function (index) {
                                EngineRequirement.setFeed(EngineRequirement.feedOptions[index].key)
                            }
                        }
                        FieldNote {
                            text: EngineRequirement.feedOptions[
                                      Math.max(0, page.indexOfKey(EngineRequirement.feedOptions,
                                                                  EngineRequirement.feed))].note
                        }

                        RFComboBox {
                            objectName: "requirementCycle"
                            Layout.preferredWidth: 320
                            label: "Power cycle"
                            enabled: EngineRequirement.cycleApplicable
                            model: EngineRequirement.cycleApplicable
                                   ? page.labels(EngineRequirement.cycleOptions)
                                   : ["Not applicable"]
                            currentIndex: EngineRequirement.cycleApplicable
                                          ? Math.max(0, page.indexOfKey(EngineRequirement.cycleOptions,
                                                                        EngineRequirement.cycle))
                                          : 0
                            onActivated: function (index) {
                                if (EngineRequirement.cycleApplicable)
                                    EngineRequirement.setCycle(EngineRequirement.cycleOptions[index].key)
                            }
                        }
                        FieldNote {
                            objectName: "requirementCycleNote"
                            text: EngineRequirement.cycleApplicable
                                  ? EngineRequirement.cycleNote
                                  : "Only a pump-fed engine has a power cycle."
                        }
                        IssueNote { text: page.issueFor("cycle") }

                        RFComboBox {
                            objectName: "requirementPriority"
                            Layout.preferredWidth: 320
                            label: "Design priority"
                            model: page.labels(EngineRequirement.priorityOptions)
                            currentIndex: page.indexOfKey(EngineRequirement.priorityOptions,
                                                          EngineRequirement.priority)
                            onActivated: function (index) {
                                EngineRequirement.setPriority(
                                    EngineRequirement.priorityOptions[index].key)
                            }
                        }
                        FieldNote {
                            text: EngineRequirement.priorityOptions[
                                      Math.max(0, page.indexOfKey(EngineRequirement.priorityOptions,
                                                                  EngineRequirement.priority))].note
                        }
                    }
                }
            }

            // ---- the record ---------------------------------------------
            RFPanel {
                Layout.preferredWidth: 400
                Layout.fillHeight: true
                title: "Recorded requirement"

                Repeater {
                    model: EngineRequirement.summaryRows
                    delegate: RowLayout {
                        id: summaryRow
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.s
                        Text {
                            Layout.preferredWidth: 130
                            text: summaryRow.modelData.label
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                            elide: Text.ElideRight
                        }
                        Text {
                            objectName: "requirementSummary_" + summaryRow.modelData.key
                            Layout.fillWidth: true
                            text: summaryRow.modelData.value
                            color: Theme.text
                            font.family: Typography.mono
                            font.pixelSize: Typography.meta
                            wrapMode: Text.WordWrap
                        }
                    }
                }

                RFDivider { Layout.fillWidth: true }

                RFSectionLabel { text: "Open decisions" }
                Text {
                    objectName: "requirementOpenDecisions"
                    Layout.fillWidth: true
                    text: EngineRequirement.openDecisions.length > 0
                          ? EngineRequirement.openDecisions.join(" · ")
                          : "None"
                    color: Theme.text
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                    wrapMode: Text.WordWrap
                }
                FieldNote { text: EngineRequirement.scopeNote }

                RFDivider { Layout.fillWidth: true }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.spacing.s
                    RFButton {
                        objectName: "requirementCopy"
                        text: "Copy JSON"
                        compact: true
                        onClicked: EngineRequirement.copyToClipboard()
                    }
                    RFButton {
                        objectName: "requirementPaste"
                        text: "Paste JSON"
                        compact: true
                        onClicked: EngineRequirement.pasteFromClipboard()
                    }
                    Item { Layout.fillWidth: true }
                    RFButton {
                        objectName: "requirementReset"
                        text: "Reset"
                        variant: "quiet"
                        compact: true
                        onClicked: EngineRequirement.reset()
                    }
                }
                FieldNote {
                    objectName: "requirementMessage"
                    text: EngineRequirement.message
                }
                Text {
                    Layout.fillWidth: true
                    text: "Fingerprint " + EngineRequirement.fingerprint
                    color: Theme.textMuted
                    font.family: Typography.mono
                    font.pixelSize: Typography.meta
                }

                Item { Layout.fillHeight: true }
            }
        }
    }
}
