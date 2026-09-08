import QtQuick
import "../theme"

/*
 * One row of a menu. Unavailable actions stay visible and legible: this build
 * has several of them, and hiding them would misrepresent the product shape.
 */
Item {
    id: root

    property string label: ""
    property string shortcut: ""
    property string note: ""
    property bool available: true
    property bool checked: false

    signal triggered()

    implicitHeight: 30
    implicitWidth: Math.max(200, labelText.implicitWidth + shortcutText.implicitWidth + 60)

    Rectangle {
        anchors.fill: parent
        radius: Metrics.radius.m
        color: root.available && mouse.containsMouse ? Theme.surfaceHover : "transparent"
        Behavior on color { ColorAnimation { duration: Motion.fast } }
    }

    RFIcon {
        id: check
        anchors.verticalCenter: parent.verticalCenter
        x: Metrics.spacing.s
        name: "check"
        width: 13
        height: 13
        visible: root.checked
        color: Theme.accent
    }

    Text {
        id: labelText
        anchors.verticalCenter: parent.verticalCenter
        x: Metrics.spacing.s + 20
        text: root.label
        color: root.available ? Theme.text : Theme.textDisabled
        font.family: Typography.sans
        font.pixelSize: Typography.body
    }

    Text {
        id: shortcutText
        anchors.verticalCenter: parent.verticalCenter
        anchors.right: parent.right
        anchors.rightMargin: Metrics.spacing.m
        text: root.available ? root.shortcut : root.note
        color: Theme.textMuted
        font.family: root.available ? Typography.mono : Typography.sans
        font.pixelSize: Typography.meta
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        enabled: root.available
        cursorShape: Qt.PointingHandCursor
        onClicked: root.triggered()
    }
}
