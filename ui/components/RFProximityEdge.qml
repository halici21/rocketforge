import QtQuick
import "../theme"

/*
 * RFProximityEdge — the one pointer-proximity treatment.
 *
 * A control's border reads three distances from the pointer: far (the
 * control's quiet border), near (a little more edge light, within `reach`
 * pixels of it), and over (the accent). It says "this is a control and you
 * are about to reach it" without any control lighting up on its own.
 *
 * Event-driven: two HoverHandlers on the control, one with a margin. No
 * global mouse polling, no per-frame work, and nothing repaints unless the
 * pointer crosses one of the two boundaries. Drop it inside any control
 * whose shape is a rounded rectangle; `active` holds the accent for a
 * checked or current control.
 */
Rectangle {
    id: edge

    property bool active: false
    property real reach: 22
    // The edge under the pointer. The accent by default; a container whose
    // own children are the controls (a segmented track) uses a quieter one.
    property color overColor: Theme.accent
    readonly property bool near: nearHandler.hovered
    readonly property bool over: overHandler.hovered

    anchors.fill: parent
    color: "transparent"
    radius: parent && parent.radius !== undefined ? parent.radius : Metrics.radius.s
    border.width: Metrics.hairline
    border.color: edge.active ? Theme.accent
                : edge.over ? edge.overColor
                : edge.near ? Theme.borderStrong
                : Theme.border

    Behavior on border.color { ColorAnimation { duration: Motion.micro } }

    HoverHandler { id: nearHandler; target: edge.parent; margin: edge.reach }
    HoverHandler { id: overHandler; target: edge.parent }
}
