import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

/*
 * RFProvenanceInspector - the shell Inspector's content for a read-only
 * evidence workspace: provenance, not results.
 *
 * It shows one reading prepared by a controller (`readout`: a kind, a title, a
 * subtitle and sections of label-over-value rows, because a locator is a
 * sentence, not a number) and nothing else. Used by the Reference Engines and
 * Propulsion Database pages, which differ only in their controller, their
 * "‹ Record" rule, any extra tool buttons and their wording.
 *
 * objectNames: <namePrefix>Inspector (the root), <namePrefix>InspectRecord,
 * <namePrefix>InspectorTitle, <namePrefix>InspectorValue.
 */
Rectangle {
    id: root

    signal closeRequested()
    signal recordRequested()

    property var readout
    property string namePrefix: ""
    // When "‹ Record" is offered: the page's own rule over `readout.kind`.
    property bool recordAvailable: false
    property string recordTooltip: ""
    property string emptyText: ""
    property string footerText: ""
    // Tool buttons placed between "‹ Record" and "Close", and when they show.
    // An explicit flag, not the children's count: a laid-out slot holding only
    // hidden buttons would still take a spacing gap and move "‹ Record".
    property alias extraTools: extra.data
    property bool extraToolsShown: false

    readonly property bool hasReadout: root.readout !== undefined && root.readout !== null
                                       && root.readout.sections !== undefined

    objectName: root.namePrefix + "Inspector"
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
                objectName: root.namePrefix + "InspectRecord"
                visible: root.hasReadout && root.recordAvailable
                text: "‹ Record"
                tooltip: root.recordTooltip
                onClicked: root.recordRequested()
            }
            RowLayout {
                id: extra
                visible: root.extraToolsShown
                spacing: Metrics.spacing.s
            }
            RFToolButton { text: "Close"; tooltip: "Close the inspector"; onClicked: root.closeRequested() }
        }

        Text {
            objectName: root.namePrefix + "InspectorTitle"
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
                                    objectName: root.namePrefix + "InspectorValue"
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
                    text: root.emptyText
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
            text: root.footerText
            wrapMode: Text.WordWrap
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
    }
}
