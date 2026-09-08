import QtQuick
import QtQuick.Shapes
import "../theme"
import "model"
import "Routing.js" as Routing

/*
 * EngineConnection - one line between two typed ports.
 *
 * Routing is orthogonal with rounded corners rather than free curves: a feed
 * system is read as a schematic, and parallel runs that share a corridor are
 * far easier to follow than a bundle of beziers. Each leg carries its own hit
 * rectangle, so a connection is as selectable as a node without a single pixel
 * of extra chrome on screen.
 *
 * The line carries no state of its own. When a solver exists it will gain mass
 * flow, pressure and temperature; today it knows only which ports it joins.
 */
Item {
    id: link

    property Item canvas: null
    property string connId: ""
    property string fromNode: ""
    property string fromPort: ""
    property string toNode: ""
    property string toPort: ""
    property string subtype: ""

    property bool hovered: false

    readonly property bool selected: EngineModel.selectionKind === "connection"
                                     && EngineModel.selectionId === connId
    readonly property bool muted: {
        EngineModel.graphRevision
        var a = EngineModel.node(fromNode)
        var b = EngineModel.node(toNode)
        return (a && !a.enabled) || (b && !b.enabled)
    }

    readonly property real stub: 18
    readonly property real cornerRadius: 9

    // Waypoints recompute whenever a node moves or the detail level changes.
    readonly property var waypoints: {
        EngineModel.geometryRevision
        EngineModel.graphRevision
        var a = EngineModel.node(fromNode)
        var b = EngineModel.node(toNode)
        if (!a || !b)
            return []
        var s1 = ComponentRegistry.port(a.type, fromPort)
        var s2 = ComponentRegistry.port(b.type, toPort)
        if (!s1 || !s2)
            return []
        return Routing.route(EngineModel.portPoint(fromNode, fromPort), s1.side,
                             EngineModel.portPoint(toNode, toPort), s2.side, stub)
    }

    readonly property string pathData: Routing.roundedPath(waypoints, cornerRadius)

    readonly property color lineColor: link.selected ? Theme.accent
                                     : ComponentRegistry.subtypeColor(link.subtype)

    opacity: link.muted ? 0.28
           : link.selected ? 1
           : link.hovered ? 1 : 0.82

    Behavior on opacity { NumberAnimation { duration: Motion.fast } }

    // ---- line ------------------------------------------------------------

    Shape {
        anchors.fill: parent
        preferredRendererType: Shape.GeometryRenderer

        ShapePath {
            strokeColor: link.lineColor
            strokeWidth: link.selected ? 2.2 : (link.hovered ? 2 : 1.5)
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap
            joinStyle: ShapePath.RoundJoin
            PathSvg { path: link.pathData }
        }
    }

    /* Where the line lands. A terminal dot is not an arrow: it reads as a
     * junction, so it can stay on at rest without turning the canvas into a
     * field of chevrons. */
    Rectangle {
        readonly property var pts: link.waypoints
        visible: pts.length >= 2
        width: 4.5
        height: 4.5
        radius: 2.25
        color: link.lineColor
        x: pts.length >= 2 ? pts[pts.length - 1].x - width / 2 : 0
        y: pts.length >= 2 ? pts[pts.length - 1].y - height / 2 : 0
    }

    /* Flow direction, revealed rather than declared. Every line carrying a
     * permanent arrowhead is how a schematic turns into a thicket, so the mark
     * is drawn only for the line under the cursor or the one being inspected -
     * which is exactly when the question "which way does this run?" is asked. */
    Item {
        id: flowMark

        readonly property var marker: Routing.flowMarker(link.waypoints, 34)

        visible: marker !== null
        opacity: (link.hovered || link.selected) ? 1 : 0
        x: marker ? marker.x : 0
        y: marker ? marker.y : 0
        rotation: marker ? marker.angle : 0

        Behavior on opacity {
            NumberAnimation { duration: Motion.fast; easing.type: Motion.standard }
        }

        Canvas {
            id: head
            anchors.centerIn: parent
            width: 16
            height: 12
            antialiasing: true

            readonly property color tone: link.lineColor
            onToneChanged: requestPaint()

            onPaint: {
                var ctx = getContext("2d")
                ctx.reset()
                ctx.fillStyle = tone
                ctx.beginPath()
                ctx.moveTo(11.5, 6)
                ctx.lineTo(4.5, 2.2)
                ctx.lineTo(6.2, 6)
                ctx.lineTo(4.5, 9.8)
                ctx.closePath()
                ctx.fill()
            }
        }
    }

    // ---- hit areas -------------------------------------------------------
    // One rectangle per orthogonal leg: exact, cheap, and it keeps the drawn
    // line free of invisible padding.

    Repeater {
        model: Math.max(0, link.waypoints.length - 1)

        delegate: MouseArea {
            required property int index

            readonly property var a: link.waypoints[index]
            readonly property var b: link.waypoints[index + 1]

            x: Math.min(a.x, b.x) - 5
            y: Math.min(a.y, b.y) - 5
            width: Math.abs(b.x - a.x) + 10
            height: Math.abs(b.y - a.y) + 10
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            acceptedButtons: Qt.LeftButton | Qt.RightButton

            onEntered: link.hovered = true
            onExited: link.hovered = false
            onPressed: function (mouse) {
                EngineModel.selectConnection(link.connId)
                if (mouse.button === Qt.RightButton && link.canvas)
                    link.canvas.requestConnectionMenu(link.connId,
                                                      mapToItem(link.canvas, mouse.x, mouse.y))
            }
            // Let the canvas keep zooming when the pointer is over a line.
            onWheel: function (wheel) { wheel.accepted = false }
        }
    }

    // ---- label -----------------------------------------------------------
    // Hidden by default: a diagram with a label on every line stops being a
    // diagram. It appears on hover and while selected.

    Rectangle {
        readonly property var pts: link.waypoints
        readonly property var anchorPoint: pts.length >= 2
                                           ? pts[Math.floor(pts.length / 2)] : { x: 0, y: 0 }

        visible: (link.hovered || link.selected) && link.subtype !== ""
        x: anchorPoint.x - width / 2
        y: anchorPoint.y - height - 6
        width: labelText.implicitWidth + Metrics.spacing.s * 2
        height: 18
        radius: Metrics.radius.xs
        color: Theme.surfaceElevated
        border.width: Metrics.hairline
        border.color: link.selected ? Theme.accent : Theme.border

        Text {
            id: labelText
            anchors.centerIn: parent
            text: link.subtype
            color: link.selected ? Theme.accent : Theme.textSecondary
            font.family: Typography.sans
            font.pixelSize: Typography.meta
            font.capitalization: Font.Capitalize
        }
    }
}
