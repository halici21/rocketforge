import QtQuick
import "../theme"

/*
 * A navigation row. Selection is carried by a short accent bar and a small
 * weight change, not by a filled block: the sidebar has to stay quiet while
 * still making the current module unmistakable.
 */
Item {
    id: root

    property string label: ""
    property bool current: false
    property bool available: true
    property string badge: ""          // e.g. "soon" on future modules
    property real indent: Metrics.spacing.l

    signal activated()

    implicitHeight: Metrics.navItemHeight
    implicitWidth: 200
    activeFocusOnTab: available

    Rectangle {
        anchors.fill: parent
        anchors.leftMargin: Metrics.spacing.s
        anchors.rightMargin: Metrics.spacing.s
        radius: Metrics.radius.m
        // The sidebar sits on the subtle surface, so both states step away
        // from it: the current row further than a hovered one.
        color: !root.available ? "transparent"
             : root.current ? Theme.surfaceHover
             : mouse.containsMouse ? Theme.surface
             : "transparent"

        Behavior on color { ColorAnimation { duration: Motion.fast } }
    }

    // Active marker.
    Rectangle {
        x: Metrics.spacing.s + 1
        anchors.verticalCenter: parent.verticalCenter
        width: 2
        height: root.current ? 14 : 0
        radius: 1
        color: Theme.accent
        opacity: root.current ? 1 : 0

        Behavior on height { NumberAnimation { duration: Motion.base; easing.type: Motion.standard } }
        Behavior on opacity { NumberAnimation { duration: Motion.base } }
    }

    Rectangle {
        anchors.fill: parent
        anchors.margins: Metrics.spacing.s - 2
        radius: Metrics.radius.m
        color: "transparent"
        border.width: Metrics.focusRing
        border.color: Theme.accent
        visible: root.activeFocus
    }

    Text {
        id: labelText
        anchors.verticalCenter: parent.verticalCenter
        x: Metrics.spacing.s + root.indent
        width: parent.width - x - Metrics.spacing.s - (badgeItem.visible ? badgeItem.width + Metrics.spacing.s : 0)
        text: root.label
        elide: Text.ElideRight
        font.family: Typography.sans
        font.pixelSize: Typography.navItem
        font.weight: root.current ? Typography.semibold : Typography.regular
        color: !root.available ? Theme.textDisabled
             : root.current ? Theme.text
             : mouse.containsMouse ? Theme.text
             : Theme.textSecondary

        Behavior on color { ColorAnimation { duration: Motion.fast } }
    }

    Text {
        id: badgeItem
        visible: root.badge !== ""
        anchors.verticalCenter: parent.verticalCenter
        anchors.right: parent.right
        anchors.rightMargin: Metrics.spacing.m + Metrics.spacing.xs
        text: root.badge
        font.family: Typography.sans
        font.pixelSize: Typography.meta
        font.weight: Typography.semibold
        font.letterSpacing: Typography.navGroupTracking
        font.capitalization: Font.AllUppercase
        color: Theme.textDisabled
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        enabled: root.available
        cursorShape: Qt.PointingHandCursor
        onClicked: root.activated()
    }

    Keys.onPressed: function (event) {
        if (event.key === Qt.Key_Return || event.key === Qt.Key_Space) {
            root.activated()
            event.accepted = true
        }
    }
}
