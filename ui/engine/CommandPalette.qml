import QtQuick
import QtQuick.Controls
import "../theme"
import "../components"
import "model"

/*
 * Ctrl+K: type a few letters, run a command. A workstation with two modes and
 * a growing component library needs a way to reach things without hunting for
 * them, and it costs one popup and a substring match.
 */
Popup {
    id: root

    signal commandInvoked(string commandId)

    property int highlighted: 0

    readonly property string query: filter.text.trim().toLowerCase()
    readonly property var matches: {
        var all = MockEngineData.commands
        if (query === "")
            return all
        return all.filter(function (c) {
            return c.label.toLowerCase().indexOf(query) >= 0
                    || c.group.toLowerCase().indexOf(query) >= 0
        })
    }

    width: 520
    height: Math.min(72 + matches.length * 32 + 8, 420)
    modal: true
    focus: true
    padding: Metrics.spacing.s
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    x: Math.round((parent.width - width) / 2)
    y: Math.round(parent.height * 0.14)

    Overlay.modal: Rectangle {
        color: Qt.rgba(0, 0, 0, Theme.isDark ? 0.45 : 0.22)
    }

    background: Rectangle {
        color: Theme.surfaceElevated
        radius: Metrics.radius.xl
        border.width: Metrics.hairline
        border.color: Theme.border
    }

    enter: Transition {
        ParallelAnimation {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Motion.fast }
            NumberAnimation { property: "y"; from: root.y - 6; to: root.y
                              duration: Motion.base; easing.type: Motion.standard }
        }
    }
    exit: Transition {
        NumberAnimation { property: "opacity"; from: 1; to: 0; duration: Motion.fast }
    }

    onOpened: {
        filter.text = ""
        highlighted = 0
        filter.forceActiveFocus()
    }

    function run(index) {
        if (index < 0 || index >= matches.length)
            return
        root.commandInvoked(matches[index].id)
        root.close()
    }

    Item {
        anchors.fill: parent

        RFTextField {
            id: filter
            x: Metrics.spacing.s
            width: parent.width - Metrics.spacing.s * 2
            placeholder: "Type a command…"
            onTextChanged: root.highlighted = 0

            Keys.onDownPressed: root.highlighted = Math.min(root.highlighted + 1,
                                                            root.matches.length - 1)
            Keys.onUpPressed: root.highlighted = Math.max(root.highlighted - 1, 0)
            Keys.onReturnPressed: root.run(root.highlighted)
            Keys.onEnterPressed: root.run(root.highlighted)
        }

        Rectangle {
            id: rule
            anchors.top: filter.bottom
            anchors.topMargin: Metrics.spacing.s
            width: parent.width
            height: Metrics.hairline
            color: Theme.divider
        }

        ListView {
            anchors.top: rule.bottom
            anchors.topMargin: Metrics.spacing.xs
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            clip: true
            model: root.matches
            currentIndex: root.highlighted
            boundsBehavior: Flickable.StopAtBounds

            ScrollBar.vertical: RFScrollBar {}

            delegate: Item {
                id: row
                required property var modelData
                required property int index

                width: ListView.view.width
                height: 32

                Rectangle {
                    anchors.fill: parent
                    anchors.leftMargin: Metrics.spacing.xs
                    anchors.rightMargin: Metrics.spacing.xs
                    radius: Metrics.radius.m
                    color: index === root.highlighted ? Theme.surfaceHover : "transparent"
                    Behavior on color { ColorAnimation { duration: Motion.fast } }
                }

                Text {
                    anchors.left: parent.left
                    anchors.leftMargin: Metrics.spacing.m
                    anchors.verticalCenter: parent.verticalCenter
                    text: row.modelData.label
                    color: index === root.highlighted ? Theme.text : Theme.textSecondary
                    font.family: Typography.sans
                    font.pixelSize: Typography.body
                }

                Text {
                    anchors.right: parent.right
                    anchors.rightMargin: Metrics.spacing.m
                    anchors.verticalCenter: parent.verticalCenter
                    text: row.modelData.group
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                HoverHandler {
                    cursorShape: Qt.PointingHandCursor
                    onHoveredChanged: if (hovered) root.highlighted = row.index
                }
                TapHandler { onTapped: root.run(row.index) }
            }
        }

        Text {
            anchors.centerIn: parent
            visible: root.matches.length === 0
            text: "No matching command"
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.bodySmall
        }
    }
}
