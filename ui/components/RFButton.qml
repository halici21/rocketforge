import QtQuick
import "../theme"

/*
 * Text button in three weights: "primary" for the one action a screen exists
 * for, "default" for everything else, "quiet" for tertiary actions.
 */
Item {
    id: root

    property string text: ""
    property string variant: "default"   // primary | default | quiet
    property string icon: ""
    property bool compact: false

    signal clicked()

    readonly property bool isPrimary: variant === "primary"
    readonly property bool isQuiet: variant === "quiet"

    implicitHeight: compact ? Metrics.controlHeightSmall : Metrics.controlHeight
    implicitWidth: row.implicitWidth + (compact ? Metrics.spacing.m : Metrics.spacing.l) * 2
    activeFocusOnTab: enabled

    Rectangle {
        anchors.fill: parent
        radius: Metrics.radius.m
        color: {
            // Unavailable actions read as a stated absence, not as a faded
            // control: this build has several of them.
            if (!root.enabled)
                return Theme.surfaceSubtle
            if (root.isPrimary)
                return mouse.pressed ? Theme.accentPressed
                     : mouse.containsMouse ? Theme.accentHover : Theme.accent
            if (root.isQuiet)
                return mouse.pressed ? Theme.surfaceHover
                     : mouse.containsMouse ? Theme.surfaceSubtle : "transparent"
            return mouse.pressed ? Theme.surfaceHover
                 : mouse.containsMouse ? Theme.surfaceHover : Theme.surfaceSubtle
        }
        border.width: !root.enabled ? Metrics.hairline
                    : (root.isPrimary || root.isQuiet) ? 0 : Metrics.hairline
        border.color: root.enabled ? Theme.border : Theme.divider

        Behavior on color { ColorAnimation { duration: Motion.fast } }
    }

    Rectangle {
        anchors.fill: parent
        anchors.margins: -2
        radius: Metrics.radius.l
        color: "transparent"
        border.width: Metrics.focusRing
        border.color: Theme.accent
        visible: root.activeFocus
    }

    Row {
        id: row
        anchors.centerIn: parent
        spacing: Metrics.spacing.s

        RFIcon {
            visible: root.icon !== ""
            name: root.icon
            width: 15
            height: 15
            anchors.verticalCenter: parent.verticalCenter
            color: !root.enabled ? Theme.textMuted
                 : root.isPrimary ? Theme.accentContrast : Theme.textSecondary
        }

        Text {
            text: root.text
            anchors.verticalCenter: parent.verticalCenter
            font.family: Typography.sans
            font.pixelSize: Typography.body
            font.weight: Typography.medium
            color: !root.enabled ? Theme.textMuted
                 : root.isPrimary ? Theme.accentContrast : Theme.text
        }
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
}
