import QtQuick
import "../theme"
import "../components"
import "model"
import "visuals"

/*
 * One entry in the component palette, and the source of a drag.
 *
 * The dragged preview is reparented to a drag layer above the whole workspace
 * on press, so it can travel over the canvas without being clipped by the
 * sidebar. The row itself dims while its component is in flight, which is the
 * only feedback the palette needs.
 */
Item {
    id: root

    property var definition: null
    property Item dragLayer: null
    property Item canvas: null

    readonly property string componentType: definition ? definition.type : ""
    readonly property bool dragging: dragArea.drag.active

    implicitHeight: 32
    implicitWidth: 200

    Rectangle {
        anchors.fill: parent
        anchors.leftMargin: Metrics.spacing.s
        anchors.rightMargin: Metrics.spacing.s
        radius: Metrics.radius.m
        color: dragArea.containsMouse && !root.dragging ? Theme.surface : "transparent"
        opacity: root.dragging ? 0.4 : 1

        Behavior on color { ColorAnimation { duration: Motion.fast } }
        Behavior on opacity { NumberAnimation { duration: Motion.fast } }
    }

    Row {
        anchors.left: parent.left
        anchors.leftMargin: Metrics.spacing.m + Metrics.spacing.xs
        anchors.right: parent.right
        anchors.rightMargin: Metrics.spacing.m
        anchors.verticalCenter: parent.verticalCenter
        spacing: Metrics.spacing.m
        opacity: root.dragging ? 0.4 : 1

        Behavior on opacity { NumberAnimation { duration: Motion.fast } }

        ComponentGlyph {
            anchors.verticalCenter: parent.verticalCenter
            width: 19
            height: 19
            glyph: root.definition ? root.definition.glyph : ""
            color: dragArea.containsMouse ? Theme.text : Theme.textMuted
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: root.definition ? root.definition.displayName : ""
            color: dragArea.containsMouse ? Theme.text : Theme.textSecondary
            font.family: Typography.sans
            font.pixelSize: Typography.navItem
            elide: Text.ElideRight

            Behavior on color { ColorAnimation { duration: Motion.fast } }
        }
    }

    MouseArea {
        id: dragArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: root.dragging ? Qt.ClosedHandCursor : Qt.OpenHandCursor
        drag.target: ghost
        drag.smoothed: false
        // The palette scrolls; without this the Flickable steals the drag.
        preventStealing: true

        onPressed: function (mouse) {
            if (!root.dragLayer)
                return
            ghost.parent = root.dragLayer
            var p = mapToItem(root.dragLayer, mouse.x, mouse.y)
            ghost.x = p.x - ghost.width / 2
            ghost.y = p.y - ghost.height / 2
        }

        onReleased: {
            if (ghost.Drag.active)
                ghost.Drag.drop()
            ghost.parent = root
        }

        // A click without a drag drops the component in the middle of the view,
        // which is quicker than dragging when the canvas is already framed.
        onClicked: {
            if (!root.dragging && root.canvas)
                root.canvas.addComponentAtCentre(root.componentType)
        }
    }

    // ---- drag preview ----------------------------------------------------

    Item {
        id: ghost
        width: 168
        height: 36
        visible: root.dragging
        opacity: 0.96

        property string componentType: root.componentType

        Drag.active: dragArea.drag.active
        Drag.source: ghost
        Drag.keys: ["rocketforge/component"]
        Drag.hotSpot.x: width / 2
        Drag.hotSpot.y: height / 2

        Rectangle {
            anchors.fill: parent
            radius: Metrics.radius.l
            color: Theme.surfaceElevated
            border.width: 1.5
            border.color: Theme.accent
        }

        Row {
            anchors.left: parent.left
            anchors.leftMargin: Metrics.spacing.m
            anchors.verticalCenter: parent.verticalCenter
            spacing: Metrics.spacing.s

            ComponentGlyph {
                anchors.verticalCenter: parent.verticalCenter
                width: 20
                height: 20
                glyph: root.definition ? root.definition.glyph : ""
                color: Theme.accent
            }

            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: root.definition ? root.definition.displayName : ""
                color: Theme.text
                font.family: Typography.sans
                font.pixelSize: Typography.bodySmall
                font.weight: Typography.medium
            }
        }
    }
}
