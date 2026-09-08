import QtQuick
import "../theme"
import "../components"
import "model"
import "visuals"

/*
 * EnginePort - one typed connection point on a component.
 *
 * Two levels of meaning, deliberately separated so the vocabulary can grow:
 *
 *     shape  ->  physical domain   (fluid, mechanical, thermal, signal)
 *     colour ->  subtype           (fuel, oxidiser, coolant, hot gas, ...)
 *
 * Shape leads because it is what survives a colour-blind reader, a greyscale
 * screenshot and a dark background; the tint is an accelerant on top of it, not
 * the message. The label spells both out on hover.
 *
 * The drawn mark stays small so the canvas stays quiet, but the item itself is
 * larger than the mark: the hit target is what the user aims at, and it is
 * generous even though nothing about it is visible.
 *
 * A port never decides anything. It reports presses to the canvas, which owns
 * the pending connection and asks EngineModel whether the pair is allowed.
 */
Item {
    id: root

    property Item canvas: null
    property string nodeId: ""
    property var portSpec: null          // registry port descriptor

    readonly property string portId: portSpec ? portSpec.id : ""
    readonly property string portType: portSpec ? portSpec.type : "fluid"
    readonly property string subtype: portSpec ? portSpec.subtype : ""
    readonly property string direction: portSpec ? portSpec.direction : "in"
    readonly property bool required: portSpec && portSpec.required === true

    readonly property bool connected: {
        EngineModel.graphRevision
        return EngineModel.isPortConnected(nodeId, portId)
    }

    // Pending-connection feedback, driven by the canvas.
    readonly property bool pending: canvas && canvas.pendingActive
    readonly property bool isPendingSource: pending && canvas.pendingNodeId === nodeId
                                            && canvas.pendingPortId === portId
    readonly property bool compatible: pending && !isPendingSource
                                       && canvas.acceptsPort(nodeId, portId)
    readonly property bool rejected: pending && !isPendingSource && !compatible

    readonly property color tint: ComponentRegistry.subtypeColor(subtype)
    readonly property bool active: compatible || hover.hovered || isPendingSource

    implicitWidth: ComponentRegistry.portHitSize
    implicitHeight: ComponentRegistry.portHitSize

    // ---- mark ------------------------------------------------------------

    PortShape {
        id: shape
        anchors.centerIn: parent
        width: ComponentRegistry.portShapeSize
        height: width
        domain: root.portType

        fillColor: root.connected ? root.tint
                 : root.active ? Theme.accentSubtle
                 : Theme.surface
        strokeColor: root.active ? Theme.accent
                   : root.connected ? root.tint
                   : root.required ? Theme.borderStrong
                   : Theme.border
        strokeWidth: root.connected || root.active ? 1.5 : 1.4

        opacity: root.rejected ? 0.25 : 1
        scale: root.active ? 1.2 : 1

        Behavior on opacity { NumberAnimation { duration: Motion.fast } }
        Behavior on scale { NumberAnimation { duration: Motion.fast; easing.type: Motion.standard } }
    }

    // Unmet required ports carry a mark, so the state is not colour alone.
    Rectangle {
        visible: root.required && !root.connected && !root.pending
        anchors.centerIn: parent
        // The triangle's centroid sits below its bounding-box centre.
        anchors.verticalCenterOffset: root.portType === "thermal" ? 1.4 : 0
        width: 3
        height: 3
        radius: 1.5
        color: Theme.warning
    }

    // ---- interaction -----------------------------------------------------

    HoverHandler {
        id: hover
        cursorShape: Qt.CrossCursor
    }

    MouseArea {
        id: area
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        preventStealing: true

        onPressed: function (mouse) {
            if (!root.canvas)
                return
            var scene = mapToItem(root.canvas.world, mouse.x, mouse.y)
            root.canvas.beginConnection(root.nodeId, root.portId, scene)
        }
        onPositionChanged: function (mouse) {
            if (!root.canvas || !root.canvas.pendingActive)
                return
            root.canvas.updateConnection(mapToItem(root.canvas.world, mouse.x, mouse.y))
        }
        onReleased: function (mouse) {
            if (!root.canvas)
                return
            root.canvas.finishConnection(mapToItem(root.canvas.world, mouse.x, mouse.y))
        }
        onCanceled: {
            if (root.canvas)
                root.canvas.cancelConnection()
        }
        // Let the canvas keep zooming when the pointer is over a port.
        onWheel: function (wheel) { wheel.accepted = false }
    }

    RFTooltip {
        text: portSpec ? portSpec.label + "  ·  " + ComponentRegistry.portTypeLabel(root.portType)
                         + (root.subtype ? " (" + root.subtype + ")" : "") : ""
        visible: hover.hovered && !root.pending
        x: (root.width - width) / 2
        y: root.height + 2
    }
}
