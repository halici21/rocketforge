import QtQuick
import "../theme"

/*
 * A Browser row: a workspace's identity AND its current state, not just its
 * name. This is what turns the rail from page navigation into engineering
 * context (the structural-recovery brief's own distinction) -- mirroring
 * EngineProjectPanel's own "Engine-01 / Gas generator - LOX/CH4" treatment,
 * not inventing a new pattern.
 *
 * The state line is sourced from each controller's own statusLabel
 * (resultChanged-scoped, already the exact text that workspace's own page
 * shows in its status chip) plus a stale suffix -- never a live input
 * value, so this row can never show a number that has since changed.
 */
Item {
    id: root

    property string label: ""
    property string stateText: ""
    property bool stale: false
    property bool current: false
    property real indent: Metrics.spacing.l

    signal activated()

    implicitHeight: stateText !== "" ? Metrics.navItemHeight + 15 : Metrics.navItemHeight
    implicitWidth: 200
    activeFocusOnTab: true

    Rectangle {
        anchors.fill: parent
        anchors.leftMargin: Metrics.spacing.s
        anchors.rightMargin: Metrics.spacing.s
        radius: Metrics.radius.m
        color: root.current ? Theme.surfaceHover
             : mouse.containsMouse ? Theme.surface
             : "transparent"

        Behavior on color { ColorAnimation { duration: Motion.fast } }
    }

    Rectangle {
        x: Metrics.spacing.s + 1
        anchors.verticalCenter: parent.verticalCenter
        width: 2
        height: root.current ? (root.stateText !== "" ? 28 : 14) : 0
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

    Column {
        anchors.verticalCenter: parent.verticalCenter
        x: Metrics.spacing.s + root.indent
        width: parent.width - x - Metrics.spacing.s
        spacing: 1

        Text {
            width: parent.width
            text: Notation.rich(root.label)
            textFormat: Notation.textFormat(root.label)
            elide: Text.ElideRight
            clip: true              // RichText does not elide
            font.family: Typography.sans
            font.pixelSize: Typography.navItem
            font.weight: root.current ? Typography.semibold : Typography.regular
            color: root.current ? Theme.text
                 : mouse.containsMouse ? Theme.text
                 : Theme.textSecondary

            Behavior on color { ColorAnimation { duration: Motion.fast } }
        }

        Text {
            visible: root.stateText !== ""
            width: parent.width
            text: root.stateText
            elide: Text.ElideRight
            font.family: Typography.sans
            font.pixelSize: Typography.meta
            color: root.stale ? Theme.warning : Theme.textMuted
        }
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
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
