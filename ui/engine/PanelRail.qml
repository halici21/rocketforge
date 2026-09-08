import QtQuick
import "../theme"
import "../components"

/*
 * What a collapsed panel leaves behind: a strip barely wider than a scrollbar,
 * carrying the name of what is folded away and a chevron pointing back towards
 * it.
 *
 * A collapse the user cannot undo is a trap, so the affordance is never a
 * hidden gesture or an edge to be found by accident - but it does not get to
 * cost a column either. The whole strip is the target.
 */
Item {
    id: root

    property string label: ""
    property string side: "left"       // which edge of the workspace it sits on

    signal restore()

    implicitWidth: Metrics.collapsedRailWidth
    width: implicitWidth

    Rectangle {
        anchors.fill: parent
        color: hover.hovered ? Theme.surfaceHover : Theme.surfaceSubtle
        Behavior on color { ColorAnimation { duration: Motion.fast } }
    }

    Rectangle {
        anchors.right: root.side === "left" ? parent.right : undefined
        anchors.left: root.side === "left" ? undefined : parent.left
        width: Metrics.hairline
        height: parent.height
        color: Theme.divider
    }

    RFIcon {
        id: chevron
        anchors.horizontalCenter: parent.horizontalCenter
        y: Metrics.spacing.m
        width: 13
        height: 13
        name: root.side === "left" ? "chevron-right" : "chevron-left"
        color: hover.hovered ? Theme.accent : Theme.textMuted
        Behavior on color { ColorAnimation { duration: Motion.fast } }
    }

    // The label runs up the strip. Hidden outright when the workspace is too
    // short for it rather than clipped to an unreadable stub.
    Item {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: chevron.bottom
        anchors.topMargin: Metrics.spacing.m
        anchors.bottom: parent.bottom
        width: parent.width
        visible: height > verticalLabel.implicitWidth + Metrics.spacing.l
        clip: true

        Text {
            id: verticalLabel
            text: root.label
            color: hover.hovered ? Theme.textSecondary : Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
            font.letterSpacing: Typography.sectionTracking
            font.capitalization: Font.AllUppercase

            rotation: 90
            transformOrigin: Item.TopLeft
            x: (parent.width + implicitHeight) / 2
            y: 0

            Behavior on color { ColorAnimation { duration: Motion.fast } }
        }
    }

    HoverHandler { id: hover; cursorShape: Qt.PointingHandCursor }
    TapHandler { onTapped: root.restore() }

    RFTooltip {
        text: "Show " + root.label.toLowerCase()
        visible: hover.hovered
        x: root.side === "left" ? root.width + 6 : -width - 6
        y: Metrics.spacing.m
    }
}
