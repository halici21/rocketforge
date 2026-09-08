import QtQuick
import QtQuick.Shapes
import "../theme"
import "../components"
import "model"
import "Routing.js" as Routing

/*
 * EngineCanvas - the drawing surface for the engine architecture.
 *
 * The board owns the view (pan, zoom, grid, marquee) and the transient
 * interactions (a connection being drawn, a component being dropped). It owns
 * no data: components and connections live in EngineModel, which is what lets
 * the same graph be shown by the project tree, the inspector and the problems
 * panel at the same time.
 *
 * The grid is drawn once per zoom level and then only translated, so panning
 * costs nothing beyond moving one item.
 */
Item {
    id: board

    property real zoom: 1
    property real minZoom: 0.3
    property real maxZoom: 2.4
    property bool snapEnabled: true
    property bool gridVisible: true
    property int gridSize: 24
    property string tool: "select"          // select | connect

    signal componentWorkspaceRequested(string nodeId)
    signal renameRequested(string nodeId)

    readonly property alias world: world
    readonly property bool empty: EngineModel.nodes.count === 0

    // ---- pending connection ---------------------------------------------
    property bool pendingActive: false
    property string pendingNodeId: ""
    property string pendingPortId: ""
    property point pendingPoint: Qt.point(0, 0)

    property bool spaceHeld: false
    clip: true
    activeFocusOnTab: true

    // =====================================================================
    // view helpers
    // =====================================================================

    function viewToWorld(p) {
        return Qt.point((p.x - world.x) / zoom, (p.y - world.y) / zoom)
    }

    function clampZoom(z) {
        return Math.max(minZoom, Math.min(maxZoom, z))
    }

    function zoomAt(factor, viewPoint) {
        var before = viewToWorld(viewPoint)
        var next = clampZoom(zoom * factor)
        if (Math.abs(next - zoom) < 0.0001)
            return
        zoom = next
        world.x = viewPoint.x - before.x * next
        world.y = viewPoint.y - before.y * next
    }

    function zoomIn() { zoomAt(1.2, Qt.point(width / 2, height / 2)) }
    function zoomOut() { zoomAt(1 / 1.2, Qt.point(width / 2, height / 2)) }

    function resetZoom() {
        var centre = viewToWorld(Qt.point(width / 2, height / 2))
        zoom = 1
        world.x = width / 2 - centre.x
        world.y = height / 2 - centre.y
    }

    /* Frame a box in the middle of the view.
     *
     * The margin scales with the viewport instead of being a fixed number of
     * pixels: a fixed inset that looks generous on a laptop is a rounding error
     * on a 2560 px display, and the composition drifts to one corner. The upper
     * zoom bound keeps a two-component sketch from being blown up until the
     * strokes look wrong - fitting is a framing operation, not a magnifier. */
    function fitBounds(bounds, maxScale) {
        if (bounds.width <= 0 || bounds.height <= 0)
            return false
        var margin = Math.max(40, Math.min(width, height) * 0.08)
        zoom = clampZoom(Math.min((width - margin * 2) / bounds.width,
                                  (height - margin * 2) / bounds.height,
                                  maxScale))
        world.x = (width - bounds.width * zoom) / 2 - bounds.x * zoom
        world.y = (height - bounds.height * zoom) / 2 - bounds.y * zoom
        return true
    }

    function fitAll() {
        if (!fitBounds(EngineModel.contentBounds(), 1.25)) {
            zoom = 1
            world.x = 0
            world.y = 0
        }
    }

    /* Fit what is picked, or the whole engine when nothing is. One action with
     * two readings beats two buttons on a bar this short, and it matches what
     * the user means by "show me this" in either case. */
    function fitSelection() {
        if (!fitBounds(EngineModel.selectionBounds(), 1.6))
            fitAll()
    }

    readonly property bool hasSelection: {
        EngineModel.selectedNodes
        return EngineModel.selectionKind === "connection"
                || EngineModel.selectedNodes.length > 0
    }

    function focusNode(nodeId) {
        var rect = EngineModel.nodeRect(nodeId)
        if (rect.width <= 0)
            return
        world.x = width / 2 - (rect.x + rect.width / 2) * zoom
        world.y = height / 2 - (rect.y + rect.height / 2) * zoom
        flash.target = nodeId
        flash.restart()
    }

    function focusSelection() {
        fitSelection()
    }

    // =====================================================================
    // node placement
    // =====================================================================

    function snap(value) {
        return snapEnabled ? Math.round(value / gridSize) * gridSize : Math.round(value)
    }

    function placeNode(id, x, y) {
        EngineModel.moveNode(id, snap(x), snap(y))
    }

    function dropComponent(type, viewPoint) {
        var size = ComponentRegistry.nodeSize(type, EngineModel.detailLevel)
        var p = viewToWorld(viewPoint)
        var id = EngineModel.addNode(type, snap(p.x - size.width / 2), snap(p.y - size.height / 2))
        if (id)
            EngineModel.selectNode(id, false)
        return id
    }

    function addComponentAtCentre(type) {
        return dropComponent(type, Qt.point(width / 2, height / 2))
    }

    function openComponentWorkspace(nodeId) {
        componentWorkspaceRequested(nodeId)
    }

    // =====================================================================
    // connections
    // =====================================================================

    function portAt(worldPoint) {
        var best = null
        var bestDistance = ComponentRegistry.portHitRadius
        for (var i = 0; i < EngineModel.nodes.count; ++i) {
            var n = EngineModel.nodes.get(i)
            var ports = ComponentRegistry.ports(n.type)
            for (var j = 0; j < ports.length; ++j) {
                var p = EngineModel.portPoint(n.nodeId, ports[j].id)
                var d = Math.sqrt(Math.pow(p.x - worldPoint.x, 2) + Math.pow(p.y - worldPoint.y, 2))
                if (d <= bestDistance) {
                    bestDistance = d
                    best = { nodeId: n.nodeId, portId: ports[j].id }
                }
            }
        }
        return best
    }

    function acceptsPort(nodeId, portId) {
        if (!pendingActive)
            return false
        return EngineModel.canConnect(pendingNodeId, pendingPortId, nodeId, portId).ok
    }

    function beginConnection(nodeId, portId, worldPoint) {
        // In connect mode a pending line is sticky, so a second press on a
        // compatible port completes it instead of starting a new one.
        if (pendingActive && (pendingNodeId !== nodeId || pendingPortId !== portId)) {
            if (acceptsPort(nodeId, portId)) {
                EngineModel.addConnection(pendingNodeId, pendingPortId, nodeId, portId)
                cancelConnection()
                return
            }
        }
        pendingNodeId = nodeId
        pendingPortId = portId
        pendingPoint = worldPoint
        pendingActive = true
        board.forceActiveFocus()
    }

    function updateConnection(worldPoint) {
        pendingPoint = worldPoint
    }

    function finishConnection(worldPoint) {
        if (!pendingActive)
            return
        var target = portAt(worldPoint)
        if (target && acceptsPort(target.nodeId, target.portId)) {
            EngineModel.addConnection(pendingNodeId, pendingPortId, target.nodeId, target.portId)
            cancelConnection()
            return
        }
        // In select mode the line lives only for the length of the drag. In
        // connect mode it stays until a compatible port is clicked, Escape is
        // pressed, or the background is clicked.
        if (tool !== "connect")
            cancelConnection()
    }

    function cancelConnection() {
        pendingActive = false
        pendingNodeId = ""
        pendingPortId = ""
    }

    // =====================================================================
    // context menus
    // =====================================================================

    function requestNodeMenu(nodeId, point) {
        nodeMenu.nodeId = nodeId
        nodeMenu.x = Math.min(point.x, width - nodeMenu.width - 8)
        nodeMenu.y = Math.min(point.y, height - nodeMenu.height - 8)
        nodeMenu.open()
    }

    function requestConnectionMenu(connId, point) {
        connectionMenu.connId = connId
        connectionMenu.x = Math.min(point.x, width - connectionMenu.width - 8)
        connectionMenu.y = Math.min(point.y, height - connectionMenu.height - 8)
        connectionMenu.open()
    }

    // =====================================================================
    // background
    // =====================================================================

    Rectangle {
        anchors.fill: parent
        color: Theme.background
        Behavior on color { ColorAnimation { duration: Motion.fast } }
    }

    /* The dot grid is painted once per zoom level into a tile that is one cell
     * larger than the viewport, then shifted by the pan remainder. Panning
     * therefore never repaints anything. */
    Canvas {
        id: grid
        visible: board.gridVisible

        readonly property real rawSpacing: board.gridSize * board.zoom
        readonly property real spacing: {
            var s = rawSpacing
            while (s < 14)
                s *= 2
            return s
        }
        readonly property color dotColor: Theme.gridLine

        function wrap(value) {
            return ((value % spacing) + spacing) % spacing
        }

        width: board.width + spacing * 2
        height: board.height + spacing * 2
        x: wrap(world.x) - spacing
        y: wrap(world.y) - spacing

        onSpacingChanged: requestPaint()
        onDotColorChanged: requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            ctx.fillStyle = dotColor
            var size = board.zoom > 1.4 ? 1.8 : 1.4
            for (var x = 0; x < width; x += spacing) {
                for (var y = 0; y < height; y += spacing)
                    ctx.fillRect(x, y, size, size)
            }
        }
    }

    // Background interaction: marquee selection, panning, zooming.
    MouseArea {
        id: background
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.MiddleButton
        hoverEnabled: true

        property bool panning: false
        property bool marquee: false
        property point origin: Qt.point(0, 0)
        property point panOrigin: Qt.point(0, 0)

        cursorShape: panning ? Qt.ClosedHandCursor
                   : board.spaceHeld ? Qt.OpenHandCursor
                   : Qt.ArrowCursor

        onPressed: function (mouse) {
            board.forceActiveFocus()
            if (board.pendingActive)
                board.cancelConnection()

            if (mouse.button === Qt.MiddleButton || board.spaceHeld) {
                panning = true
                origin = Qt.point(mouse.x, mouse.y)
                panOrigin = Qt.point(world.x, world.y)
                return
            }
            marquee = true
            origin = Qt.point(mouse.x, mouse.y)
            selectionRect.x = mouse.x
            selectionRect.y = mouse.y
            selectionRect.width = 0
            selectionRect.height = 0
        }

        onPositionChanged: function (mouse) {
            if (panning) {
                world.x = panOrigin.x + (mouse.x - origin.x)
                world.y = panOrigin.y + (mouse.y - origin.y)
            } else if (marquee) {
                selectionRect.x = Math.min(origin.x, mouse.x)
                selectionRect.y = Math.min(origin.y, mouse.y)
                selectionRect.width = Math.abs(mouse.x - origin.x)
                selectionRect.height = Math.abs(mouse.y - origin.y)
            }
        }

        onReleased: function (mouse) {
            if (marquee) {
                if (selectionRect.width > 4 && selectionRect.height > 4)
                    board.selectInRect(selectionRect.x, selectionRect.y,
                                        selectionRect.width, selectionRect.height)
                else
                    EngineModel.clearSelection()
            }
            panning = false
            marquee = false
            selectionRect.width = 0
            selectionRect.height = 0
        }

        onWheel: function (wheel) {
            board.zoomAt(wheel.angleDelta.y > 0 ? 1.12 : 1 / 1.12,
                          Qt.point(wheel.x, wheel.y))
        }
    }

    function selectInRect(vx, vy, vw, vh) {
        var topLeft = viewToWorld(Qt.point(vx, vy))
        var bottomRight = viewToWorld(Qt.point(vx + vw, vy + vh))
        var ids = []
        for (var i = 0; i < EngineModel.nodes.count; ++i) {
            var n = EngineModel.nodes.get(i)
            var size = ComponentRegistry.nodeSize(n.type, EngineModel.detailLevel)
            if (n.x < bottomRight.x && n.x + size.width > topLeft.x
                    && n.y < bottomRight.y && n.y + size.height > topLeft.y)
                ids.push(n.nodeId)
        }
        EngineModel.setSelectedNodes(ids)
    }

    // =====================================================================
    // world
    // =====================================================================

    Item {
        id: world
        transformOrigin: Item.TopLeft
        scale: board.zoom

        // Connections sit under the components they join.
        Repeater {
            model: EngineModel.connections

            delegate: EngineConnection {
                required property var model
                canvas: board
                connId: model.connId
                fromNode: model.fromNode
                fromPort: model.fromPort
                toNode: model.toNode
                toPort: model.toPort
                subtype: model.subtype
            }
        }

        // The line that follows the cursor while a connection is being drawn.
        Shape {
            id: pendingShape
            visible: board.pendingActive
            preferredRendererType: Shape.GeometryRenderer

            readonly property var pending: {
                if (!board.pendingActive)
                    return []
                var n = EngineModel.node(board.pendingNodeId)
                if (!n)
                    return []
                var spec = ComponentRegistry.port(n.type, board.pendingPortId)
                if (!spec)
                    return []
                return Routing.routeToPoint(EngineModel.portPoint(board.pendingNodeId,
                                                                  board.pendingPortId),
                                            spec.side, board.pendingPoint, 18)
            }

            ShapePath {
                strokeColor: Theme.accent
                strokeWidth: 1.6
                fillColor: "transparent"
                capStyle: ShapePath.RoundCap
                joinStyle: ShapePath.RoundJoin
                strokeStyle: ShapePath.DashLine
                dashPattern: [4, 3]
                PathSvg { path: Routing.roundedPath(pendingShape.pending, 9) }
            }
        }

        Repeater {
            model: EngineModel.nodes

            delegate: EngineNode {
                required property var model
                canvas: board
                nodeId: model.nodeId
                type: model.type
                name: model.name
                meta: model.meta
                nodeEnabled: model.enabled
                x: model.x
                y: model.y
            }
        }

        // Brief highlight used when the problems panel or the tree focuses an item.
        Rectangle {
            id: flashRect
            visible: flash.running
            radius: Metrics.radius.l + 4
            color: "transparent"
            border.width: 2
            border.color: Theme.accent
            opacity: 0

            readonly property var rect: EngineModel.nodeRect(flash.target)
            x: rect.x - 6
            y: rect.y - 6
            width: rect.width + 12
            height: rect.height + 12
        }
    }

    SequentialAnimation {
        id: flash
        property string target: ""

        NumberAnimation { target: flashRect; property: "opacity"; to: 1; duration: Motion.fast }
        PauseAnimation { duration: 420 }
        NumberAnimation { target: flashRect; property: "opacity"; to: 0; duration: Motion.slow }
    }

    // Marquee rectangle lives in view space so it stays a constant weight.
    Rectangle {
        id: selectionRect
        visible: width > 0 && height > 0
        color: Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.08)
        border.width: 1
        border.color: Theme.accent
        radius: 2
    }

    // =====================================================================
    // palette drops
    // =====================================================================

    DropArea {
        id: dropArea
        anchors.fill: parent
        keys: ["rocketforge/component"]

        property string componentType: drag.source && drag.source.componentType
                                       ? drag.source.componentType : ""

        onDropped: function (drop) {
            if (dropArea.componentType) {
                board.dropComponent(dropArea.componentType, Qt.point(drop.x, drop.y))
                drop.accept()
            }
        }
    }

    // Drop preview: shows exactly where the component will land, snapped.
    Item {
        visible: dropArea.containsDrag && dropArea.componentType !== ""

        readonly property var size: dropArea.componentType
                                    ? ComponentRegistry.nodeSize(dropArea.componentType,
                                                                 EngineModel.detailLevel)
                                    : { width: 0, height: 0 }
        readonly property var origin: {
            var p = board.viewToWorld(Qt.point(dropArea.drag.x, dropArea.drag.y))
            return { x: board.snap(p.x - size.width / 2), y: board.snap(p.y - size.height / 2) }
        }

        x: origin.x * board.zoom + world.x
        y: origin.y * board.zoom + world.y
        width: size.width * board.zoom
        height: size.height * board.zoom

        RFDashedFrame {
            anchors.fill: parent
            radius: Metrics.radius.l
            strokeColor: Theme.accent
            label: dropArea.componentType ? ComponentRegistry.displayName(dropArea.componentType) : ""
        }
    }

    // =====================================================================
    // empty state
    // =====================================================================

    Column {
        anchors.centerIn: parent
        spacing: Metrics.spacing.s
        visible: board.empty && !dropArea.containsDrag
        opacity: 0.9

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "Build your engine architecture"
            color: Theme.textSecondary
            font.family: Typography.sans
            font.pixelSize: Typography.groupLabel + 2
            font.weight: Typography.medium
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "Drag components from the palette, or load the demo engine."
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.bodySmall
        }

        Item { width: 1; height: Metrics.spacing.s }

        RFButton {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "Load demo engine"
            variant: "default"
            compact: true
            onClicked: {
                EngineModel.loadDemo()
                board.fitAll()
            }
        }
    }

    // =====================================================================
    // context menus
    // =====================================================================

    RFMenu {
        id: nodeMenu
        property string nodeId: ""
        dismissOnAnyOutsidePress: true
        width: 220

        readonly property var node: {
            EngineModel.graphRevision
            return nodeId ? EngineModel.node(nodeId) : null
        }

        Column {
            width: parent.width

            RFMenuItem {
                width: parent.width
                label: "Open component workspace"
                onTriggered: { nodeMenu.close(); board.openComponentWorkspace(nodeMenu.nodeId) }
            }
            RFMenuItem {
                width: parent.width
                label: "Rename…"
                onTriggered: { nodeMenu.close(); board.renameRequested(nodeMenu.nodeId) }
            }
            RFMenuItem {
                width: parent.width
                label: "Duplicate"
                shortcut: "Ctrl+D"
                onTriggered: { nodeMenu.close(); EngineModel.duplicateNode(nodeMenu.nodeId) }
            }
            RFMenuItem {
                width: parent.width
                label: nodeMenu.node && !nodeMenu.node.enabled ? "Enable" : "Disable"
                onTriggered: {
                    var enabled = nodeMenu.node ? nodeMenu.node.enabled : true
                    EngineModel.setNodeEnabled(nodeMenu.nodeId, !enabled)
                    nodeMenu.close()
                }
            }
            RFMenuItem {
                width: parent.width
                label: "Disconnect"
                available: {
                    EngineModel.graphRevision
                    return nodeMenu.nodeId
                            ? EngineModel.connectionsForNode(nodeMenu.nodeId).length > 0 : false
                }
                note: "no connections"
                onTriggered: { nodeMenu.close(); EngineModel.disconnectNode(nodeMenu.nodeId) }
            }

            Rectangle {
                width: parent.width
                height: Metrics.hairline
                color: Theme.divider
            }

            RFMenuItem {
                width: parent.width
                label: "Delete"
                shortcut: "Del"
                onTriggered: { nodeMenu.close(); EngineModel.removeNode(nodeMenu.nodeId) }
            }
        }
    }

    RFMenu {
        id: connectionMenu
        property string connId: ""
        dismissOnAnyOutsidePress: true
        width: 200

        Column {
            width: parent.width

            RFMenuItem {
                width: parent.width
                label: "Delete connection"
                shortcut: "Del"
                onTriggered: { connectionMenu.close(); EngineModel.removeConnection(connectionMenu.connId) }
            }
        }
    }

    // =====================================================================
    // keyboard
    // =====================================================================

    Keys.onPressed: function (event) {
        if (event.isAutoRepeat) {
            event.accepted = false
            return
        }
        switch (event.key) {
        case Qt.Key_Space:
            board.spaceHeld = true
            event.accepted = true
            return
        case Qt.Key_Escape:
            board.cancelConnection()
            EngineModel.clearSelection()
            event.accepted = true
            return
        case Qt.Key_Delete:
        case Qt.Key_Backspace:
            EngineModel.deleteSelection()
            event.accepted = true
            return
        case Qt.Key_F:
            board.focusSelection()
            event.accepted = true
            return
        case Qt.Key_A:
            if (event.modifiers & Qt.ControlModifier) {
                EngineModel.selectAll()
                event.accepted = true
            }
            return
        case Qt.Key_D:
            if (event.modifiers & Qt.ControlModifier) {
                EngineModel.duplicateSelection()
                event.accepted = true
            }
            return
        case Qt.Key_0:
            if (event.modifiers & Qt.ControlModifier) {
                board.fitAll()
                event.accepted = true
            }
            return
        }
        event.accepted = false
    }

    Keys.onReleased: function (event) {
        if (event.key === Qt.Key_Space && !event.isAutoRepeat) {
            board.spaceHeld = false
            event.accepted = true
        }
    }
}
