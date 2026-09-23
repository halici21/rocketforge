import QtQuick
import QtQuick.Controls
import "../theme"

/*
 * A tooltip that matches the panels rather than the platform.
 */
ToolTip {
    id: root

    delay: 420
    timeout: 6000
    padding: 0

    background: Rectangle {
        color: Theme.surfaceElevated
        radius: Metrics.radius.m
        border.width: Metrics.hairline
        border.color: Theme.border
    }

    contentItem: Text {
        text: Notation.rich(root.text)
        textFormat: Notation.textFormat(root.text)
        color: Theme.textSecondary
        font.family: Typography.sans
        font.pixelSize: Typography.bodySmall
        leftPadding: Metrics.spacing.s
        rightPadding: Metrics.spacing.s
        topPadding: Metrics.spacing.xs + 1
        bottomPadding: Metrics.spacing.xs + 1
    }

    enter: Transition {
        NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Motion.fast }
    }
    exit: Transition {
        NumberAnimation { property: "opacity"; from: 1; to: 0; duration: Motion.fast }
    }
}
