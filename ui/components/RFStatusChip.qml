import QtQuick
import "../theme"

/*
 * A small state marker. Carries a dot and a word, never a number that matters.
 * Tone drives the dot only: state is never communicated by colour alone.
 */
Rectangle {
    id: root

    property string text: ""
    property string tone: "neutral"   // neutral | accent | success | warning | error
    property bool showDot: true

    readonly property color toneColor: {
        switch (tone) {
        case "accent":  return Theme.accent
        case "success": return Theme.success
        case "warning": return Theme.warning
        case "error":   return Theme.error
        default:        return Theme.textMuted
        }
    }

    implicitHeight: Metrics.chipHeight
    implicitWidth: row.implicitWidth + Metrics.spacing.s * 2
    radius: Metrics.radius.s
    color: Theme.surfaceSubtle
    border.width: Metrics.hairline
    border.color: Theme.divider

    Row {
        id: row
        anchors.centerIn: parent
        spacing: Metrics.spacing.xs + 2

        Rectangle {
            width: 5
            height: 5
            radius: 2.5
            visible: root.showDot
            color: root.toneColor
            anchors.verticalCenter: parent.verticalCenter
            Behavior on color { ColorAnimation { duration: Motion.base } }
        }

        Text {
            text: Notation.rich(root.text)
            textFormat: Notation.textFormat(root.text)
            color: Theme.textSecondary
            font.family: Typography.sans
            font.pixelSize: Typography.status
            font.weight: Typography.medium
            anchors.verticalCenter: parent.verticalCenter
        }
    }

    Behavior on color { ColorAnimation { duration: Motion.fast } }
}
