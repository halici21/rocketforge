import QtQuick
import "../theme"

/*
 * RFBottomDrawer — the bottom drawer of the shared workspace grammar.
 *
 * Supporting data (a sweep's table, a list of stations) under the plots it
 * supports. Closed, a one-line handle names what is inside and how much of it
 * ("Sweep data · 41 rows"); open, it takes `drawerHeight` and pushes the view
 * above it (the owner binds `Layout.preferredHeight: drawer.implicitHeight`).
 * As with RFWorkspaceDrawer the size changes at once; only the panel's
 * opacity and a few pixels of travel animate.
 */
Item {
    id: root

    property bool open: false
    property string title: "Data"
    property string summary: ""
    property real drawerHeight: 300
    readonly property real handleHeight: 32
    default property alias content: panelBody.data

    implicitHeight: root.open ? root.drawerHeight : root.handleHeight

    onOpenChanged: {
        if (root.open && Motion.animated) {
            panelBody.arrive = 0
            arrival.restart()
        } else {
            panelBody.arrive = 1
        }
    }

    Rectangle {
        id: handle
        objectName: "bottomDrawerHandle"
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: root.handleHeight
        radius: Metrics.radius.m
        color: Theme.surfaceSubtle
        activeFocusOnTab: true

        Accessible.role: Accessible.Button
        Accessible.name: (root.open ? "Hide " : "Show ") + root.title
        Accessible.description: root.summary

        RFProximityEdge { active: handle.activeFocus }

        Row {
            anchors.left: parent.left
            anchors.leftMargin: Metrics.spacing.m
            anchors.verticalCenter: parent.verticalCenter
            spacing: Metrics.spacing.s

            Text {
                // Points the way the drawer will move.
                text: root.open ? "▾" : "▴"
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.body
            }
            Text {
                text: root.title + (root.summary !== "" ? "  ·  " + root.summary : "")
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.bodySmall
            }
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: root.open = !root.open
        }
        Keys.onSpacePressed: root.open = !root.open
        Keys.onReturnPressed: root.open = !root.open
    }

    Item {
        id: panelBody
        objectName: "bottomDrawerBody"
        anchors.top: handle.bottom
        anchors.topMargin: Metrics.spacing.s
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        visible: root.open

        property real arrive: 1
        opacity: arrive
        transform: Translate { y: (1 - panelBody.arrive) * Motion.panelShift }
        NumberAnimation {
            id: arrival
            target: panelBody
            property: "arrive"
            to: 1
            duration: Motion.panel
            easing.type: Motion.standard
        }
    }
}
