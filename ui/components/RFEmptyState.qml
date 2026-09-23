import QtQuick
import "../theme"

/*
 * RFEmptyState - the message shown where content will eventually live: a
 * status tag, one sentence of explanation, and the planned contents as chips.
 * The surrounding page decides how much room to give it.
 */
Column {
    id: root

    property string tag: ""
    property string title: ""
    property string body: ""
    property var bullets: []

    spacing: Metrics.spacing.m

    RFStatusChip {
        visible: root.tag !== ""
        text: root.tag
        tone: "neutral"
        showDot: false
        anchors.horizontalCenter: parent.horizontalCenter
    }

    Text {
        width: parent.width
        text: Notation.rich(root.title)
        textFormat: Notation.textFormat(root.title)
        horizontalAlignment: Text.AlignHCenter
        color: Theme.text
        font.family: Typography.sans
        font.pixelSize: Typography.groupLabel + 3
        font.weight: Typography.medium
    }

    Text {
        width: parent.width
        visible: root.body !== ""
        text: root.body
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.WordWrap
        lineHeight: Typography.proseLineHeight
        lineHeightMode: Text.ProportionalHeight
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.bodySmall
    }

    Item {
        width: 1
        height: root.bullets.length > 0 ? Metrics.spacing.xs : 0
    }

    Row {
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: Metrics.spacing.s

        Repeater {
            model: root.bullets
            delegate: RFStatusChip {
                required property var modelData
                text: modelData
                showDot: false
            }
        }
    }
}
