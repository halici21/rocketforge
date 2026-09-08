import QtQuick
import "../theme"

/*
 * A square, quiet action button. The background only appears on interaction or
 * while the action it represents is the active one.
 */
Item {
    id: root

    property string icon: ""
    property string tooltip: ""
    property bool active: false
    property real size: Metrics.iconButton
    property real iconSize: 16

    signal clicked()

    implicitWidth: size
    implicitHeight: size
    activeFocusOnTab: enabled
    opacity: enabled ? 1 : 0.4

    Rectangle {
        anchors.fill: parent
        radius: Metrics.radius.m
        color: !root.enabled ? "transparent"
             : mouse.pressed ? Theme.surfaceHover
             : root.active ? Theme.surfaceSubtle
             : mouse.containsMouse ? Theme.surfaceHover
             : "transparent"
        border.width: Metrics.hairline
        border.color: root.active ? Theme.border : "transparent"

        Behavior on color { ColorAnimation { duration: Motion.fast } }
        Behavior on border.color { ColorAnimation { duration: Motion.fast } }
    }

    // Focus ring, drawn outside the fill so it never shifts the layout.
    Rectangle {
        anchors.fill: parent
        anchors.margins: -2
        radius: Metrics.radius.l
        color: "transparent"
        border.width: Metrics.focusRing
        border.color: Theme.accent
        visible: root.activeFocus
    }

    RFIcon {
        anchors.centerIn: parent
        name: root.icon
        width: root.iconSize
        height: root.iconSize
        color: !root.enabled ? Theme.textDisabled
             : root.active ? Theme.text
             : mouse.containsMouse ? Theme.text
             : Theme.textSecondary
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        enabled: root.enabled
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }

    Keys.onPressed: function (event) {
        if (event.key === Qt.Key_Return || event.key === Qt.Key_Space) {
            root.clicked()
            event.accepted = true
        }
    }

    RFTooltip {
        text: root.tooltip
        visible: root.tooltip !== "" && mouse.containsMouse
        x: (root.width - width) / 2
        y: root.height + 6
    }
}
