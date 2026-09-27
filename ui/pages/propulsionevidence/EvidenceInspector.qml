import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * The Propulsion Database's Inspector content: provenance, not results.
 *
 * Two readings, both prepared by the controller from the stored record: the
 * record itself (identity, formulation, each source with its locator, access,
 * shipping and rights, and the record's notes), or one stored field (its exact
 * stored value, the unit as printed, how it entered the record, where it is
 * printed, and the source) -- or, for a missing field, its reason. Rows are
 * label over value, because a locator is a sentence, not a number.
 */
Rectangle {
    id: root

    signal closeRequested()

    readonly property var readout: PropulsionEvidence.inspectionReadout
    readonly property bool hasReadout: root.readout !== undefined && root.readout !== null
                                       && root.readout.sections !== undefined

    objectName: "evidenceInspector"
    color: Theme.surfaceSubtle

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.spacing.l
        spacing: Metrics.spacing.m

        RowLayout {
            Layout.fillWidth: true
            spacing: Metrics.spacing.s

            RFSectionLabel { text: "Inspector  ·  Provenance" }
            Item { Layout.fillWidth: true }
            RFToolButton {
                objectName: "evidenceInspectRecord"
                visible: root.hasReadout && root.readout.kind === "datum"
                text: "‹ Record"
                tooltip: "Back to the record's sources and notes"
                onClicked: PropulsionEvidence.inspectRecord()
            }
            RFToolButton { text: "Close"; tooltip: "Close the inspector"; onClicked: root.closeRequested() }
        }

        Text {
            objectName: "evidenceInspectorTitle"
            Layout.fillWidth: true
            visible: root.hasReadout
            text: root.hasReadout ? root.readout.title : ""
            wrapMode: Text.WordWrap
            color: Theme.text
            font.family: Typography.sans
            font.pixelSize: Typography.readoutMedium
            font.weight: Typography.medium
        }
        Text {
            Layout.fillWidth: true
            visible: root.hasReadout
            text: root.hasReadout ? root.readout.subtitle : ""
            color: Theme.textSecondary
            font.family: Typography.mono
            font.pixelSize: Typography.meta
        }

        RFDivider { Layout.fillWidth: true; visible: root.hasReadout }

        Flickable {
            id: scroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentWidth: width
            contentHeight: sections.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: RFScrollBar {}

            ColumnLayout {
                id: sections
                width: scroll.width
                spacing: Metrics.spacing.l

                Repeater {
                    model: root.hasReadout ? root.readout.sections : []

                    delegate: ColumnLayout {
                        id: section
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.s

                        RFSectionLabel { text: section.modelData.title }

                        Repeater {
                            model: section.modelData.rows
                            delegate: ColumnLayout {
                                id: row
                                required property var modelData
                                Layout.fillWidth: true
                                spacing: 1

                                Text {
                                    Layout.fillWidth: true
                                    visible: row.modelData.label !== ""
                                    text: row.modelData.label
                                    color: Theme.textMuted
                                    font.family: Typography.sans
                                    font.pixelSize: Typography.meta
                                }
                                Text {
                                    objectName: "evidenceInspectorValue"
                                    Layout.fillWidth: true
                                    text: row.modelData.value
                                    wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                                    color: Theme.text
                                    font.family: Typography.sans
                                    font.pixelSize: Typography.bodySmall
                                    lineHeight: Typography.proseLineHeight
                                    lineHeightMode: Text.ProportionalHeight
                                }
                            }
                        }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    visible: !root.hasReadout
                    text: "Select a record in the library to inspect its sources."
                    wrapMode: Text.WordWrap
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                }
            }
        }

        RFDivider { Layout.fillWidth: true }
        Text {
            Layout.fillWidth: true
            text: "Stored evidence, shown as stored. Nothing here is computed, converted or solved."
            wrapMode: Text.WordWrap
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
    }
}
