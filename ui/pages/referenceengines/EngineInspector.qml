import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * The Reference Engines Inspector content: provenance, not results.
 *
 * One reading at a time, each prepared by the ReferenceEngines controller: the
 * configuration (lineage, operating points, cited sources), one assertion (as
 * printed, its value kind, scope, every recorded condition -- an unknown one
 * stays "Unknown" -- its locator and its source's rights), one source
 * (authority and shipping, kept apart), one capability (its gaps and caveats),
 * or the topology graph, a component or a connection. Rows are label over
 * value, because a locator is a sentence, not a number.
 */
Rectangle {
    id: root

    signal closeRequested()

    readonly property var readout: ReferenceEngines.inspectionReadout
    readonly property bool hasReadout: root.readout !== undefined && root.readout !== null
                                       && root.readout.sections !== undefined

    objectName: "engineInspector"
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
                objectName: "engineInspectRecord"
                visible: root.hasReadout && root.readout.kind !== "configuration"
                text: "‹ Record"
                tooltip: "Back to the configuration's identity and sources"
                onClicked: ReferenceEngines.inspectRecord()
            }
            RFToolButton {
                objectName: "engineInspectSource"
                visible: root.hasReadout && root.readout.kind === "assertion" && root.readout.sourceId !== undefined
                text: "Source ›"
                tooltip: "This value's source: its authority and its rights, separately"
                onClicked: ReferenceEngines.inspectSource(root.readout.sourceId)
            }
            RFToolButton { text: "Close"; tooltip: "Close the inspector"; onClicked: root.closeRequested() }
        }

        Text {
            objectName: "engineInspectorTitle"
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
                                    objectName: "engineInspectorValue"
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
                    text: "Select an engine configuration in the library to inspect it."
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
            text: "Shipped reference evidence, shown as recorded. Nothing here is computed, converted, edited or solved, and no record drives a design or a solver."
            wrapMode: Text.WordWrap
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
    }
}
