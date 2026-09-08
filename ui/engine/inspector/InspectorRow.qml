import QtQuick
import "../../theme"
import "../../components"

/*
 * A property line: name on the left, value on the right. Numeric values use
 * the monospaced face so a column of them lines up; unavailable values are an
 * em dash rather than a zero.
 */
Item {
    id: root

    property string label: ""
    property string value: ""
    property bool numeric: false
    property bool interactive: false
    property bool highlighted: false

    signal activated()

    width: parent ? parent.width : 0
    height: 24

    Rectangle {
        anchors.fill: parent
        anchors.leftMargin: -Metrics.spacing.xs
        anchors.rightMargin: -Metrics.spacing.xs
        radius: Metrics.radius.s
        color: root.interactive && hover.hovered ? Theme.surfaceHover : "transparent"
        Behavior on color { ColorAnimation { duration: Motion.fast } }
    }

    Text {
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
        width: parent.width * 0.45
        text: root.label
        elide: Text.ElideRight
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.bodySmall
    }

    Text {
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        width: parent.width * 0.55
        horizontalAlignment: Text.AlignRight
        text: root.value
        elide: Text.ElideRight
        color: root.value === "—" ? Theme.textDisabled
             : root.highlighted ? Theme.accent : Theme.text
        font.family: root.numeric ? Typography.mono : Typography.sans
        font.pixelSize: root.numeric ? Typography.readoutSmall : Typography.bodySmall
    }

    HoverHandler {
        id: hover
        enabled: root.interactive
        cursorShape: Qt.PointingHandCursor
    }

    TapHandler {
        enabled: root.interactive
        onTapped: root.activated()
    }
}
