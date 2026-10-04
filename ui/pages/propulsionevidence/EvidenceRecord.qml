import QtQuick
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"
import "../../data"

/*
 * The selected evidence record, as the object of the page.
 *
 * Identity first, then the four dimensions -- each its own cell with its own
 * status word, never counted or combined -- then the formulation exactly as
 * the source lists it, then whatever the record says it lacks. Every number is
 * the controller's exact stored text; the composition bar is the stored mass
 * fraction itself (full width = 1), never renormalised, and a missing fraction
 * draws no bar. Clicking a value or a missing field inspects it.
 *
 * Under the strip, one quiet NASA CEA line: "Not checked" until the person
 * asks. The check probes the installed library and solves nothing; its
 * blockers, when it finds any, are listed right there. "Open in
 * Thermochemistry" exists only after a check found the record executable and
 * equal to a Thermochemistry case -- it is created then, not merely shown.
 */
ColumnLayout {
    id: root

    spacing: Metrics.spacing.l

    function inspect(key) {
        PropulsionEvidence.inspectDatum(key)
        ShellContext.inspectorOpen = true
    }

    // ---- identity ----------------------------------------------------------
    RFPanel {
        Layout.fillWidth: true
        contentSpacing: Metrics.spacing.s

        RowLayout {
            Layout.fillWidth: true
            spacing: Metrics.spacing.m

            ColumnLayout {
                Layout.fillWidth: true
                spacing: Metrics.spacing.xs

                RFSectionLabel { text: PropulsionEvidence.recordKind === "PROPELLANT" ? "Propellant record" : "Reference record" }

                Text {
                    objectName: "evidenceRecordTitle"
                    Layout.fillWidth: true
                    text: PropulsionEvidence.recordTitle
                    wrapMode: Text.WordWrap
                    color: Theme.text
                    font.family: Typography.sans
                    font.pixelSize: Typography.readoutLarge
                    font.weight: Typography.medium
                }
                Text {
                    objectName: "evidenceRecordId"
                    text: PropulsionEvidence.selectedRecordId
                    color: Theme.textSecondary
                    font.family: Typography.mono
                    font.pixelSize: Typography.bodySmall
                }
            }

            RFToolButton {
                objectName: "evidenceProvenanceButton"
                Layout.alignment: Qt.AlignTop
                text: "Sources and provenance  ›"
                tooltip: "Open the record's sources, locators, access and shipping in the Inspector"
                checked: ShellContext.inspectorOpen && PropulsionEvidence.inspectionKey === ""
                onClicked: {
                    PropulsionEvidence.inspectRecord()
                    ShellContext.inspectorOpen = true
                }
            }
        }

        Text {
            Layout.fillWidth: true
            visible: PropulsionEvidence.formulationLine !== ""
            text: PropulsionEvidence.formulationLine
            wrapMode: Text.WordWrap
            color: Theme.textSecondary
            font.family: Typography.sans
            font.pixelSize: Typography.body
        }
        Text {
            objectName: "evidenceSourceLine"
            Layout.fillWidth: true
            text: PropulsionEvidence.sourceLine
            wrapMode: Text.WordWrap
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.bodySmall
        }
    }

    // ---- the four dimensions, independently ------------------------------
    ColumnLayout {
        Layout.fillWidth: true
        spacing: Metrics.spacing.s

        RFSectionLabel { text: "What this record can support, per dimension" }

        GridLayout {
            id: strip
            objectName: "evidenceCapabilityStrip"
            Layout.fillWidth: true
            // Four cells in one row while each keeps a readable width; below
            // that, a deliberate 2 x 2 rather than smaller type.
            columns: root.width >= 900 ? 4 : 2
            columnSpacing: Metrics.spacing.s
            rowSpacing: Metrics.spacing.s

            Repeater {
                model: PropulsionEvidence.capabilities

                delegate: Rectangle {
                    id: cell
                    required property string dimension
                    required property string dimensionName
                    required property string statusLabel
                    required property string tone
                    required property bool applicable
                    required property string capabilityNote

                    objectName: "capability_" + cell.dimension
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.preferredWidth: 1
                    implicitHeight: cellColumn.implicitHeight + Metrics.spacing.m * 2
                    radius: Metrics.radius.m
                    color: cell.applicable ? Theme.surface : Theme.surfaceSubtle
                    border.width: Metrics.hairline
                    border.color: cell.applicable ? Theme.border : Theme.divider

                    ColumnLayout {
                        id: cellColumn
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: Metrics.spacing.m
                        spacing: Metrics.spacing.xs

                        Text {
                            Layout.fillWidth: true
                            text: cell.dimension + "  ·  " + cell.dimensionName
                            elide: Text.ElideRight
                            color: Theme.textSecondary
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                            font.weight: Typography.medium
                            font.letterSpacing: Typography.sectionTracking
                        }
                        RowLayout {
                            spacing: Metrics.spacing.s
                            Rectangle {
                                visible: cell.tone !== "none"
                                Layout.alignment: Qt.AlignVCenter
                                width: 6
                                height: 6
                                radius: 3
                                color: cell.tone === "warning" ? Theme.warning : Theme.textSecondary
                            }
                            Text {
                                objectName: "capabilityStatus_" + cell.dimension
                                text: cell.statusLabel
                                color: cell.applicable ? Theme.text : Theme.textMuted
                                font.family: Typography.sans
                                font.pixelSize: Typography.body
                                font.weight: cell.applicable ? Typography.medium : Typography.regular
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            visible: cell.capabilityNote !== ""
                            text: cell.capabilityNote
                            wrapMode: Text.WordWrap
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                            lineHeight: Typography.proseLineHeight
                            lineHeightMode: Text.ProportionalHeight
                        }
                    }
                }
            }
        }

        // ---- NASA CEA: asked, never assumed (EV-3) --------------------------
        ColumnLayout {
            objectName: "evidenceCompatibility"
            Layout.fillWidth: true
            Layout.topMargin: Metrics.spacing.xs
            visible: PropulsionEvidence.compatibilityState !== ""
            spacing: Metrics.spacing.xs

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.spacing.s

                Text {
                    Layout.alignment: Qt.AlignVCenter
                    text: "NASA CEA"
                    color: Theme.textSecondary
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                    font.weight: Typography.medium
                    font.letterSpacing: Typography.sectionTracking
                }
                // The state in words; the dot only repeats it.
                RFStatusChip {
                    objectName: "evidenceCompatibilityState"
                    Layout.alignment: Qt.AlignVCenter
                    text: PropulsionEvidence.compatibilityLabel
                    tone: PropulsionEvidence.compatibilityTone
                    showDot: PropulsionEvidence.compatibilityTone !== "none"
                }
                Item { Layout.fillWidth: true }
                RFButton {
                    objectName: "evidenceCompatibilityCheck"
                    Layout.alignment: Qt.AlignVCenter
                    visible: PropulsionEvidence.canCheckCompatibility
                    compact: true
                    text: PropulsionEvidence.compatibilityChecked ? "Check again"
                                                                  : "Check CEA compatibility"
                    onClicked: PropulsionEvidence.checkCompatibility()
                }
                Loader {
                    Layout.alignment: Qt.AlignVCenter
                    active: PropulsionEvidence.canOpenInThermochemistry
                    visible: active
                    sourceComponent: RFButton {
                        objectName: "evidenceOpenThermochemistry"
                        compact: true
                        variant: "primary"
                        text: "Open in Thermochemistry"
                        onClicked: PropulsionEvidence.openInThermochemistry()
                    }
                }
            }

            Text {
                objectName: "evidenceCompatibilityMeaning"
                Layout.fillWidth: true
                text: PropulsionEvidence.compatibilityIdentity !== ""
                      ? PropulsionEvidence.compatibilityMeaning + "  "
                        + PropulsionEvidence.compatibilityIdentity
                      : PropulsionEvidence.compatibilityMeaning
                wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
                lineHeight: Typography.proseLineHeight
                lineHeightMode: Text.ProportionalHeight
            }

            // After a check stopped at the access gate: what is withheld, kept
            // apart from scientific blockers -- nothing was assessed.
            ColumnLayout {
                objectName: "evidenceAccessRestrictions"
                Layout.fillWidth: true
                visible: PropulsionEvidence.accessRestrictionCount > 0
                spacing: 2

                Repeater {
                    model: PropulsionEvidence.accessRestrictions
                    delegate: Text {
                        required property string restrictionText
                        objectName: "evidenceAccessRestriction"
                        Layout.fillWidth: true
                        text: "Access  ·  " + restrictionText
                        wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                        color: Theme.textSecondary
                        font.family: Typography.sans
                        font.pixelSize: Typography.bodySmall
                    }
                }
            }

            // After a check: the blockers are the content (R1 section 7).
            ColumnLayout {
                objectName: "evidenceCompatibilityBlockers"
                Layout.fillWidth: true
                visible: PropulsionEvidence.compatibilityBlockerCount > 0
                spacing: 2

                Repeater {
                    model: PropulsionEvidence.compatibilityBlockers
                    delegate: Text {
                        required property string blockerCode
                        required property string blockerText
                        objectName: "evidenceCompatibilityBlocker"
                        Layout.fillWidth: true
                        text: blockerCode + "  ·  " + blockerText
                        wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                        color: Theme.text
                        font.family: Typography.sans
                        font.pixelSize: Typography.bodySmall
                    }
                }
            }

            Text {
                objectName: "evidenceOpenUnavailable"
                Layout.fillWidth: true
                visible: PropulsionEvidence.openUnavailableReason !== ""
                text: PropulsionEvidence.openUnavailableReason
                wrapMode: Text.WordWrap
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.bodySmall
            }
        }
    }

    // ---- formulation, as the source lists it -------------------------------
    RFPanel {
        objectName: "evidenceComposition"
        Layout.fillWidth: true
        visible: PropulsionEvidence.hasPropellant
        title: "Composition  ·  mass fraction as stored"
        contentSpacing: 0

        Repeater {
            model: PropulsionEvidence.composition

            delegate: Rectangle {
                id: ingredient
                required property string datumKey
                required property string name
                required property string definition
                required property string valueText
                required property string unit
                required property string valueStatus
                required property bool missing
                required property real share

                readonly property bool inspected: PropulsionEvidence.inspectionKey === ingredient.datumKey

                Layout.fillWidth: true
                implicitHeight: ingredientRow.implicitHeight + Metrics.spacing.s * 2
                radius: Metrics.radius.s
                color: ingredient.inspected ? Theme.surfaceHover
                       : ingredientArea.containsMouse ? Theme.surfaceSubtle : "transparent"

                RowLayout {
                    id: ingredientRow
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin: Metrics.spacing.s
                    anchors.rightMargin: Metrics.spacing.s
                    spacing: Metrics.spacing.m

                    // A fixed name column: the stored fraction's bar keeps the
                    // rest, so every bar shares one scale across the rows.
                    ColumnLayout {
                        readonly property real nameWidth: Math.min(280, root.width * 0.28)
                        Layout.preferredWidth: nameWidth
                        Layout.maximumWidth: nameWidth
                        Layout.minimumWidth: nameWidth
                        spacing: 2
                        Text {
                            Layout.fillWidth: true
                            text: ingredient.name
                            elide: Text.ElideRight
                            color: Theme.text
                            font.family: Typography.mono
                            font.pixelSize: Typography.body
                        }
                        Text {
                            Layout.fillWidth: true
                            visible: ingredient.definition !== ""
                            text: ingredient.definition
                            wrapMode: Text.WordWrap
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                    }

                    // The stored fraction, on a 0 - 1 scale. No bar for a
                    // missing fraction: absence is not a zero.
                    Item {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 10
                        Rectangle {
                            anchors.fill: parent
                            visible: ingredient.share >= 0     // no track either: absence is not a scale
                            radius: 2
                            color: Theme.surfaceSunken
                            border.width: Metrics.hairline
                            border.color: Theme.divider
                        }
                        Rectangle {
                            visible: ingredient.share >= 0
                            width: parent.width * Math.max(0, ingredient.share)
                            height: parent.height
                            radius: 2
                            color: ingredient.inspected ? Theme.accent : Theme.textMuted
                            opacity: ingredient.inspected ? 1 : 0.7
                        }
                    }

                    Text {
                        // a missing fraction's reason is words, given the room they need
                        Layout.preferredWidth: ingredient.missing ? implicitWidth : 120
                        horizontalAlignment: Text.AlignRight
                        text: ingredient.valueText
                        color: ingredient.missing ? Theme.textSecondary : Theme.text
                        font.family: Typography.mono
                        font.pixelSize: Typography.readoutSmall
                    }
                    Text {
                        Layout.preferredWidth: 110
                        text: ingredient.unit !== "" ? ingredient.unit : ""
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                    Text {
                        Layout.preferredWidth: 96
                        text: ingredient.valueStatus
                        color: Theme.textMuted
                        font.family: Typography.mono
                        font.pixelSize: Typography.meta
                    }
                }

                MouseArea {
                    id: ingredientArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.inspect(ingredient.datumKey)
                }
            }
        }

        Text {
            Layout.fillWidth: true
            Layout.topMargin: Metrics.spacing.s
            text: "Bars show each stored fraction as a share of the whole, on a 0 – 1 scale (a wt% value as its hundredth); the numbers are as printed. Click an ingredient for its source, locator and status; every other stored value is in Evidence data below."
            wrapMode: Text.WordWrap
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
    }

    // ---- what the record lacks, in its own words ---------------------------
    RFPanel {
        objectName: "evidenceGaps"
        Layout.fillWidth: true
        // Only when the record actually has something to say here: no empty
        // warning panel is reserved for a record with nothing missing.
        visible: PropulsionEvidence.missingCount + PropulsionEvidence.blockerCount
                 + PropulsionEvidence.rightsCount > 0
        title: "Missing, blocked and withheld"
        contentSpacing: Metrics.spacing.s

        Repeater {
            model: PropulsionEvidence.missing
            delegate: Rectangle {
                id: gap
                required property string datumKey
                required property string field
                required property string reason
                required property string missingNote

                Layout.fillWidth: true
                implicitHeight: gapColumn.implicitHeight + Metrics.spacing.s * 2
                radius: Metrics.radius.s
                color: PropulsionEvidence.inspectionKey === gap.datumKey ? Theme.surfaceHover
                       : gapArea.containsMouse ? Theme.surfaceSubtle : "transparent"

                ColumnLayout {
                    id: gapColumn
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin: Metrics.spacing.s
                    anchors.rightMargin: Metrics.spacing.s
                    spacing: 2
                    RowLayout {
                        spacing: Metrics.spacing.m
                        Text {
                            text: gap.field
                            color: Theme.text
                            font.family: Typography.sans
                            font.pixelSize: Typography.body
                        }
                        Text {
                            objectName: "missingReason"
                            text: "Missing  ·  " + gap.reason
                            color: Theme.textSecondary
                            font.family: Typography.mono
                            font.pixelSize: Typography.meta
                        }
                    }
                    Text {
                        Layout.fillWidth: true
                        visible: gap.missingNote !== ""
                        text: gap.missingNote
                        wrapMode: Text.WordWrap
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.bodySmall
                    }
                }
                MouseArea {
                    id: gapArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.inspect(gap.datumKey)
                }
            }
        }

        Repeater {
            model: PropulsionEvidence.blockers
            delegate: Text {
                required property string blockerText
                Layout.fillWidth: true
                text: "Blocker  ·  " + blockerText
                wrapMode: Text.WordWrap
                color: Theme.text
                font.family: Typography.sans
                font.pixelSize: Typography.body
            }
        }

        Repeater {
            model: PropulsionEvidence.rights
            delegate: Text {
                required property string sourceId
                required property string policy
                required property string meaning
                Layout.fillWidth: true
                text: sourceId + "  ·  " + policy + "  ·  " + meaning
                wrapMode: Text.WordWrap
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.body
            }
        }
    }

    // ---- notes, as stored ----------------------------------------------------
    RFPanel {
        Layout.fillWidth: true
        visible: PropulsionEvidence.recordNotes !== "" || PropulsionEvidence.payloadNote !== ""
        title: "Notes"
        contentSpacing: Metrics.spacing.s

        Text {
            Layout.fillWidth: true
            visible: PropulsionEvidence.payloadNote !== ""
            text: PropulsionEvidence.payloadNote
            wrapMode: Text.WordWrap
            color: Theme.text
            font.family: Typography.sans
            font.pixelSize: Typography.body
        }
        Text {
            Layout.fillWidth: true
            visible: PropulsionEvidence.recordNotes !== ""
            text: PropulsionEvidence.recordNotes
            wrapMode: Text.WordWrap
            lineHeight: Typography.proseLineHeight
            lineHeightMode: Text.ProportionalHeight
            color: Theme.textSecondary
            font.family: Typography.sans
            font.pixelSize: Typography.body
        }
    }
}
