import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../theme"
import "../../components"
import "../model"
import "../visuals"

/*
 * Creating an engine: a name and an architecture, nothing more. Propulsion
 * requirements and sizing belong to a later phase, so the dialog stays small
 * and honest about what it does - it starts an empty canvas with a cycle in
 * mind, it does not lay one out.
 */
Popup {
    id: root

    signal created(string name, string architecture)

    property int selectedIndex: 1     // gas generator reads as the default case

    readonly property var template_: MockEngineData.cycleTemplates[selectedIndex]

    width: 680
    height: 460
    modal: true
    focus: true
    anchors.centerIn: Overlay.overlay
    closePolicy: Popup.CloseOnEscape
    padding: Metrics.spacing.xxl

    Overlay.modal: Rectangle {
        color: Qt.rgba(0, 0, 0, Theme.isDark ? 0.55 : 0.28)
    }

    background: Rectangle {
        color: Theme.surface
        radius: Metrics.radius.xl
        border.width: Metrics.hairline
        border.color: Theme.border
    }

    enter: Transition {
        ParallelAnimation {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Motion.base }
            NumberAnimation { property: "scale"; from: 0.985; to: 1; duration: Motion.base
                              easing.type: Motion.standard }
        }
    }
    exit: Transition {
        NumberAnimation { property: "opacity"; from: 1; to: 0; duration: Motion.fast }
    }

    onOpened: nameField.forceActiveFocus()

    ColumnLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.l

        Column {
            Layout.fillWidth: true
            spacing: 2

            Text {
                text: "New engine"
                color: Theme.text
                font.family: Typography.sans
                font.pixelSize: Typography.pageTitle - 3
                font.weight: Typography.semibold
            }
            Text {
                text: "Name the engine and choose the cycle it will be built around."
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.bodySmall
            }
        }

        RFTextField {
            id: nameField
            Layout.preferredWidth: 280
            label: "Name"
            text: "Engine-02"
        }

        RFSectionLabel { text: "Architecture" }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Metrics.spacing.l

            // ---- cycle list ----
            Rectangle {
                Layout.preferredWidth: 210
                Layout.fillHeight: true
                color: Theme.surfaceSubtle
                radius: Metrics.radius.l
                border.width: Metrics.hairline
                border.color: Theme.border

                Column {
                    anchors.fill: parent
                    anchors.margins: Metrics.spacing.xs

                    Repeater {
                        model: MockEngineData.cycleTemplates

                        delegate: RFNavItem {
                            required property var modelData
                            required property int index
                            width: parent.width
                            indent: Metrics.spacing.s
                            label: modelData.name
                            current: index === root.selectedIndex
                            onActivated: root.selectedIndex = index
                        }
                    }
                }
            }

            // ---- preview ----
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: Theme.surfaceSubtle
                radius: Metrics.radius.l
                border.width: Metrics.hairline
                border.color: Theme.border

                CycleSchematic {
                    anchors.fill: parent
                    anchors.margins: Metrics.spacing.l
                    anchors.bottomMargin: description.height + Metrics.spacing.l
                    boxes: root.template_.boxes
                    links: root.template_.links
                }

                Text {
                    id: description
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.margins: Metrics.spacing.l
                    text: root.template_.description
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: Metrics.spacing.s

            Text {
                Layout.fillWidth: true
                text: "The cycle is recorded on the engine. Components are not placed for you."
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            RFButton {
                text: "Cancel"
                variant: "quiet"
                compact: true
                onClicked: root.close()
            }

            RFButton {
                text: "Create engine"
                variant: "primary"
                compact: true
                onClicked: {
                    root.created(nameField.text, root.template_.name)
                    root.close()
                }
            }
        }
    }
}
