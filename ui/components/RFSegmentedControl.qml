import QtQuick
import "../theme"

/*
 * RFSegmentedControl - a small set of mutually exclusive choices.
 *
 * The selection is a single surface that slides between segments: the movement
 * is what tells you the state changed, so the colours can stay quiet. Used for
 * the "given quantity" choice and for theme selection.
 */
Item {
    id: root

    property var model: []
    property int currentIndex: 0
    property bool useMonoFont: false
    // Segments that exist in the product but are not available yet. They stay
    // visible and legible, and say why on hover.
    property var disabledIndices: []
    property string disabledNote: ""

    signal selected(int index)

    readonly property real inset: 3
    readonly property real segmentWidth: model.length > 0
                                       ? (width - inset * 2) / model.length : 0

    implicitHeight: Metrics.controlHeight
    implicitWidth: Math.max(240, model.length * 76)
    activeFocusOnTab: true

    Rectangle {
        id: track
        anchors.fill: parent
        radius: Metrics.radius.l
        color: Theme.surfaceSubtle
        border.width: Metrics.hairline
        border.color: root.activeFocus ? Theme.accent : Theme.border

        Behavior on color { ColorAnimation { duration: Motion.fast } }
        Behavior on border.color { ColorAnimation { duration: Motion.fast } }
    }

    // The moving selection.
    Rectangle {
        id: thumb
        x: root.inset + root.currentIndex * root.segmentWidth
        y: root.inset
        width: root.segmentWidth
        height: root.height - root.inset * 2
        radius: Metrics.radius.m
        color: Theme.surfaceElevated
        border.width: Metrics.hairline
        border.color: Theme.borderStrong

        Behavior on x {
            NumberAnimation { duration: Motion.base; easing.type: Motion.standard }
        }
    }

    Row {
        anchors.fill: parent
        anchors.margins: root.inset

        Repeater {
            model: root.model

            delegate: Item {
                id: segment
                required property var modelData
                required property int index

                readonly property bool isCurrent: index === root.currentIndex
                readonly property bool available: root.disabledIndices.indexOf(index) < 0

                width: root.segmentWidth
                height: root.height - root.inset * 2

                Text {
                    anchors.centerIn: parent
                    text: Notation.rich(segment.modelData)
                    textFormat: Notation.textFormat(segment.modelData)
                    color: !segment.available ? Theme.textDisabled
                         : segment.isCurrent ? Theme.text
                         : hover.hovered ? Theme.textSecondary
                         : Theme.textMuted
                    font.family: root.useMonoFont ? Typography.mono : Typography.sans
                    font.pixelSize: Typography.bodySmall
                    font.weight: segment.isCurrent ? Typography.semibold : Typography.regular

                    Behavior on color { ColorAnimation { duration: Motion.fast } }
                }

                HoverHandler {
                    id: hover
                    cursorShape: segment.available ? Qt.PointingHandCursor : Qt.ArrowCursor
                }

                TapHandler {
                    enabled: segment.available
                    onTapped: {
                        root.currentIndex = segment.index
                        root.selected(segment.index)
                    }
                }

                RFTooltip {
                    text: root.disabledNote
                    visible: !segment.available && hover.hovered && root.disabledNote !== ""
                    x: (segment.width - width) / 2
                    y: segment.height + 6
                }
            }
        }
    }

    Keys.onLeftPressed: if (currentIndex > 0) { currentIndex--; selected(currentIndex) }
    Keys.onRightPressed: if (currentIndex < model.length - 1) { currentIndex++; selected(currentIndex) }
}
