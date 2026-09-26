import QtQuick
import "../theme"

/*
 * RFDrawerHandle — the edge a collapsed drawer leaves behind.
 *
 * A slim strip on the drawer's edge that still says what the drawer holds:
 * its title and a one-line summary of the case (the inputs the result was
 * solved from), so collapsing the inputs never hides which case is on
 * screen. Click, Space or Return toggles the drawer; the chevron says which
 * way it will move. The same pointer-proximity edge as every other control.
 *
 * The drawer itself is the owner's content; this is only its handle, so the
 * left inputs drawer, like the right inspector and the bottom dock, has one
 * open/closed state with one writer.
 */
Rectangle {
    id: root

    property string title: "Inputs"
    property string summary: ""
    property bool open: false
    property string edge: "left"            // the edge the drawer lives on

    signal toggled()

    implicitWidth: 34
    radius: Metrics.radius.m
    color: Theme.surfaceSubtle
    activeFocusOnTab: true

    Accessible.role: Accessible.Button
    Accessible.name: (root.open ? "Hide " : "Show ") + root.title
    Accessible.description: root.summary

    RFProximityEdge { active: root.activeFocus }

    Text {
        id: chevron
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: Metrics.spacing.s
        // Points the way the drawer will move.
        text: (root.edge === "left") === root.open ? "‹" : "›"
        color: Theme.textSecondary
        font.family: Typography.sans
        font.pixelSize: Typography.body
    }

    // Title and summary, read bottom-to-top along the edge.
    Text {
        anchors.centerIn: parent
        rotation: -90
        width: root.height - 3 * Metrics.spacing.l
        horizontalAlignment: Text.AlignHCenter
        elide: Text.ElideRight
        text: root.title.toUpperCase() + (root.summary !== "" ? "   ·   " + root.summary : "")
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.meta
        font.letterSpacing: 0.4
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: root.toggled()
    }

    Keys.onSpacePressed: root.toggled()
    Keys.onReturnPressed: root.toggled()
}
