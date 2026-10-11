import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * A RocketForge rendering of one shipped topology graph -- never the source's
 * figure, and nothing the graph does not hold.
 *
 * Every node and every edge is a row of the controller's models; positions and
 * curve control points come from its deterministic layout, which is
 * presentation only: the connections are the evidence, where a box sits is
 * not. The provenance (original drawing or third-party reconstruction), the
 * graph's own incompleteness and its known omissions are stated above the
 * drawing, in words. Engine-owned components have a solid outline; stage,
 * vehicle and ambient components a dashed one and their owner named. Edge
 * kinds differ by line pattern and are named in the legend -- never by colour
 * alone. Clicking a box or an edge's handle inspects it; nothing can be moved,
 * added or removed.
 */
ColumnLayout {
    id: root

    spacing: Metrics.spacing.s

    property real zoom: 1.0
    readonly property real minZoom: 0.4
    readonly property real maxZoom: 1.6

    function inspectNode(id) { ReferenceEngines.inspectNode(id); ShellContext.inspectorOpen = true }
    function inspectEdge(id) { ReferenceEngines.inspectEdge(id); ShellContext.inspectorOpen = true }
    function fit() {
        if (ReferenceEngines.graphWidth > 0 && viewport.width > 0)
            root.zoom = Math.max(root.minZoom, Math.min(1.0, (viewport.width - 2) / ReferenceEngines.graphWidth))
    }
    // The dash pattern each relationship is drawn with; the legend repeats it.
    function dashFor(kind) {
        switch (kind) {
        case "FLUID_FLOW": return []
        case "MECHANICAL_SHAFT": return [7, 3]
        case "GEARED_DRIVE": return [2, 3]
        case "MECHANICAL_LINKAGE": return [5, 5]
        case "CONTROL_ACTUATION": return [8, 3, 2, 3]
        case "ELECTRICAL_POWER": return [1, 3]
        }
        return [3, 3]
    }
    function widthFor(kind) { return kind === "MECHANICAL_SHAFT" || kind === "GEARED_DRIVE" ? 2 : 1.25 }

    Connections {
        target: ReferenceEngines
        function onGraphChanged() { root.zoom = 1.0; viewport.contentX = 0; viewport.contentY = 0 }
    }

    // ---- provenance, completeness, layout: in words, before the drawing ----
    Rectangle {
        objectName: "topologyReconstructionBanner"
        Layout.fillWidth: true
        visible: ReferenceEngines.graphReconstruction
        implicitHeight: reconText.implicitHeight + Metrics.spacing.s * 2
        radius: Metrics.radius.s
        color: Theme.surfaceSubtle
        border.width: 1.5
        border.color: Theme.warning

        Text {
            id: reconText
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: Metrics.spacing.m
            anchors.rightMargin: Metrics.spacing.m
            text: "<b>Third-party reconstruction.</b> This graph rests on a drawing made by someone other than the "
                  + "engine's maker or agency, not on an original schematic"
                  + (ReferenceEngines.graphDrawnBy !== "" ? " (" + ReferenceEngines.graphDrawnBy + ")" : "")
                  + ". Its connections may differ from the hardware."
            textFormat: Text.StyledText
            wrapMode: Text.WordWrap
            color: Theme.text
            font.family: Typography.sans
            font.pixelSize: Typography.bodySmall
        }
    }

    Flow {
        Layout.fillWidth: true
        spacing: Metrics.spacing.s

        RFStatusChip {
            objectName: "topologyProvenance"
            text: ReferenceEngines.graphProvenance
            showDot: false
        }
        RFStatusChip {
            objectName: "topologyCompleteness"
            text: ReferenceEngines.graphCompleteness
            showDot: false
        }
        RFStatusChip {
            visible: ReferenceEngines.graphIsUnit
            text: "Drawn for the whole " + ReferenceEngines.graphScope
            showDot: false
        }
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: Metrics.spacing.s

        Text {
            objectName: "topologyLayoutNote"
            Layout.fillWidth: true
            text: "Connectivity is evidence; position is not. RocketForge laid these boxes out for reading."
            wrapMode: Text.WordWrap
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }

        // View only, and outside the drawing so they never cover a wire:
        // zoom and reset never change the graph.
        Row {
            spacing: 2
            RFToolButton { objectName: "topologyZoomOut"; text: "−"; tooltip: "Zoom out"
                onClicked: root.zoom = Math.max(root.minZoom, root.zoom / 1.2) }
            RFToolButton { objectName: "topologyZoomIn"; text: "+"; tooltip: "Zoom in"
                onClicked: root.zoom = Math.min(root.maxZoom, root.zoom * 1.2) }
            RFToolButton { objectName: "topologyFit"; text: "Fit"; tooltip: "Fit the drawing to the width"
                onClicked: root.fit() }
            RFToolButton { objectName: "topologyReset"; text: "Reset"; tooltip: "Back to full size, top left"
                onClicked: { root.zoom = 1.0; viewport.contentX = 0; viewport.contentY = 0 } }
        }
    }

    // ---- the drawing -------------------------------------------------------
    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: Math.min(560, ReferenceEngines.graphHeight * root.zoom + 2)
        Layout.minimumHeight: 160
        radius: Metrics.radius.m
        color: Theme.surfaceSunken
        border.width: Metrics.hairline
        border.color: Theme.divider

        Flickable {
            id: viewport
            objectName: "topologyViewport"
            anchors.fill: parent
            anchors.margins: 1
            clip: true
            contentWidth: ReferenceEngines.graphWidth * root.zoom
            contentHeight: ReferenceEngines.graphHeight * root.zoom
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.horizontal: RFScrollBar {}
            ScrollBar.vertical: RFScrollBar {}

            Item {
                id: drawing
                width: ReferenceEngines.graphWidth
                height: ReferenceEngines.graphHeight
                transform: Scale { xScale: root.zoom; yScale: root.zoom }

                Canvas {
                    id: wires
                    objectName: "topologyEdges"
                    anchors.fill: parent
                    antialiasing: true
                    // Repaint on change only: the graph, the selection, the theme.
                    readonly property color ink: Theme.textSecondary
                    readonly property color mark: Theme.accent
                    readonly property string selectedEdge: ReferenceEngines.selectedEdgeId
                    readonly property string selectedNode: ReferenceEngines.selectedNodeId
                    onInkChanged: requestPaint()
                    onMarkChanged: requestPaint()
                    onSelectedEdgeChanged: requestPaint()
                    onSelectedNodeChanged: requestPaint()
                    Connections {
                        target: ReferenceEngines
                        function onGraphChanged() { wires.requestPaint() }
                    }
                    Connections {
                        target: edgeData
                        function onCountChanged() { wires.requestPaint() }
                    }

                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.reset()
                        for (var i = 0; i < edgeData.count; ++i) {
                            var e = edgeData.itemAt(i)
                            if (!e) continue
                            var hot = e.edgeId === selectedEdge
                                      || (selectedNode !== "" && (e.source === selectedNode || e.target === selectedNode))
                            ctx.strokeStyle = hot ? mark : ink
                            ctx.fillStyle = hot ? mark : ink
                            ctx.lineWidth = root.widthFor(e.edgeKind) + (e.edgeId === selectedEdge ? 1 : 0)
                            ctx.setLineDash(root.dashFor(e.edgeKind))
                            // An orthogonal wire through the gaps between boxes,
                            // its corners softened; the points are the controller's.
                            var p = e.points
                            ctx.beginPath()
                            ctx.moveTo(p[0], p[1])
                            for (var k = 2; k + 3 < p.length; k += 2) {
                                var r = Math.min(5, (Math.abs(p[k] - p[k - 2]) + Math.abs(p[k + 1] - p[k - 1])) / 2,
                                                 (Math.abs(p[k + 2] - p[k]) + Math.abs(p[k + 3] - p[k + 1])) / 2)
                                ctx.arcTo(p[k], p[k + 1], p[k + 2], p[k + 3], r)
                            }
                            ctx.lineTo(p[p.length - 2], p[p.length - 1])
                            ctx.stroke()
                            // A filled arrowhead marks direction, on every kind.
                            ctx.setLineDash([])
                            ctx.beginPath()
                            ctx.moveTo(e.x3, e.y3)
                            ctx.lineTo(e.ax, e.ay)
                            ctx.lineTo(e.bx, e.by)
                            ctx.closePath()
                            ctx.fill()
                        }
                    }
                }

                // The edges' data, read by the Canvas, plus a handle on each.
                Repeater {
                    id: edgeData
                    model: ReferenceEngines.graphEdges

                    delegate: Item {
                        id: edge
                        required property string edgeId
                        required property string source
                        required property string target
                        required property string edgeKind
                        required property string kindWord
                        required property string carrier
                        required property string role
                        required property string fromLabel
                        required property string toLabel
                        required property string path
                        // the wire's corner points, as the controller placed them (x y x y ...)
                        readonly property var points: edge.path.split(" ").map(Number)
                        required property real x3
                        required property real y3
                        required property real mx
                        required property real my
                        required property real ax
                        required property real ay
                        required property real bx
                        required property real by

                        readonly property bool selected: ReferenceEngines.selectedEdgeId === edge.edgeId

                        objectName: "edgeHandle_" + edge.edgeId
                        x: edge.mx - 8
                        y: edge.my - 8
                        width: 16
                        height: 16
                        // Every wire, and so its handle, runs in the gaps between
                        // boxes: above them, a handle never covers a label.
                        z: 2
                        activeFocusOnTab: true
                        Accessible.role: Accessible.Button
                        Accessible.name: edge.kindWord + " from " + edge.fromLabel + " to " + edge.toLabel
                                         + ": " + edge.role
                        Keys.onReturnPressed: root.inspectEdge(edge.edgeId)
                        Keys.onSpacePressed: root.inspectEdge(edge.edgeId)

                        Rectangle {
                            anchors.centerIn: parent
                            width: edge.selected || handleArea.containsMouse || edge.activeFocus ? 9 : 6
                            height: width
                            rotation: 45
                            color: edge.selected ? Theme.accent : Theme.surface
                            border.width: 1
                            border.color: edge.selected || edge.activeFocus ? Theme.accent : Theme.textSecondary
                        }
                        MouseArea {
                            id: handleArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.inspectEdge(edge.edgeId)
                        }
                        ToolTip.visible: handleArea.containsMouse
                        ToolTip.delay: 400
                        ToolTip.text: edge.fromLabel + " → " + edge.toLabel + "\n" + edge.kindWord + (edge.carrier !== "" ? " · " + edge.carrier : "") + "\n" + edge.role
                    }
                }

                Repeater {
                    model: ReferenceEngines.graphNodes

                    delegate: Item {
                        id: node
                        required property string nodeId
                        required property string nodeLabel
                        required property string nodeType
                        required property string ownershipWord
                        required property bool engineOwned
                        required property real nx
                        required property real ny
                        required property real nw
                        required property real nh

                        readonly property bool selected: ReferenceEngines.selectedNodeId === node.nodeId

                        objectName: "node_" + node.nodeId
                        x: node.nx
                        y: node.ny
                        width: node.nw
                        height: node.nh
                        z: 1
                        activeFocusOnTab: true
                        Accessible.role: Accessible.Button
                        Accessible.name: node.nodeLabel + ", " + node.ownershipWord
                        Keys.onReturnPressed: root.inspectNode(node.nodeId)
                        Keys.onSpacePressed: root.inspectNode(node.nodeId)

                        Rectangle {
                            anchors.fill: parent
                            radius: Metrics.radius.s
                            color: node.selected ? Theme.surfaceHover
                                   : node.engineOwned ? Theme.surface : Theme.surfaceSubtle
                            border.width: node.selected ? 2 : (node.engineOwned ? 1 : 0)
                            border.color: node.selected ? Theme.accent : Theme.borderStrong
                        }
                        // Not the engine's: a dashed outline, and its owner named.
                        RFDashedFrame {
                            anchors.fill: parent
                            visible: !node.engineOwned && !node.selected
                            radius: Metrics.radius.s
                            strokeColor: Theme.textMuted
                        }
                        RFProximityEdge { active: node.activeFocus }

                        Column {
                            anchors.fill: parent
                            anchors.margins: 5
                            spacing: 1
                            Text {
                                width: parent.width
                                text: node.nodeLabel
                                wrapMode: Text.WordWrap
                                maximumLineCount: 2
                                elide: Text.ElideRight
                                color: Theme.text
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                                font.weight: node.selected ? Typography.semibold : Typography.medium
                            }
                            Text {
                                width: parent.width
                                text: node.engineOwned ? node.nodeType : node.ownershipWord + " · " + node.nodeType
                                elide: Text.ElideRight
                                color: Theme.textMuted
                                font.family: Typography.sans
                                font.pixelSize: 10
                            }
                        }
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.inspectNode(node.nodeId)
                        }
                    }
                }
            }
        }
    }

    // ---- legend: pattern and words, never colour alone ---------------------
    Flow {
        objectName: "topologyLegend"
        Layout.fillWidth: true
        spacing: Metrics.spacing.m

        Repeater {
            model: [["FLUID_FLOW", "Fluid flow"], ["MECHANICAL_SHAFT", "Mechanical shaft"],
                    ["GEARED_DRIVE", "Geared drive"], ["MECHANICAL_LINKAGE", "Mechanical linkage"],
                    ["CONTROL_ACTUATION", "Control actuation"], ["ELECTRICAL_POWER", "Electrical power"]]
            delegate: Row {
                required property var modelData
                visible: ReferenceEngines.graphKinds.indexOf(modelData[1]) >= 0
                spacing: Metrics.spacing.xs
                Canvas {
                    width: 28
                    height: 12
                    anchors.verticalCenter: parent.verticalCenter
                    readonly property color ink: Theme.textSecondary
                    onInkChanged: requestPaint()
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.reset()
                        ctx.strokeStyle = ink
                        ctx.lineWidth = root.widthFor(modelData[0])
                        ctx.setLineDash(root.dashFor(modelData[0]))
                        ctx.beginPath(); ctx.moveTo(1, 6); ctx.lineTo(27, 6); ctx.stroke()
                    }
                }
                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: modelData[1]
                    color: Theme.textSecondary
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }
        }
        Row {
            spacing: Metrics.spacing.xs
            Rectangle { width: 22; height: 12; radius: 2; color: Theme.surface; border.width: 1; border.color: Theme.borderStrong
                anchors.verticalCenter: parent.verticalCenter }
            Text { text: "Engine component"; color: Theme.textSecondary; font.family: Typography.sans
                font.pixelSize: Typography.meta; anchors.verticalCenter: parent.verticalCenter }
        }
        Row {
            visible: ReferenceEngines.graphHasNonEngine
            spacing: Metrics.spacing.xs
            RFDashedFrame { width: 22; height: 12; radius: 2; strokeColor: Theme.textMuted
                anchors.verticalCenter: parent.verticalCenter }
            Text { text: "Stage, vehicle or ambient: not the engine's"; color: Theme.textSecondary
                font.family: Typography.sans; font.pixelSize: Typography.meta; anchors.verticalCenter: parent.verticalCenter }
        }
        Text {
            text: "◆ handle: inspect an edge"
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
    }

    // ---- what the graph itself says it leaves out ---------------------------
    ColumnLayout {
        objectName: "topologyOmissions"
        Layout.fillWidth: true
        Layout.topMargin: Metrics.spacing.xs
        visible: !ReferenceEngines.graphComplete
        spacing: 2

        Text {
            text: "Known omissions, as the graph records them"
            color: Theme.textSecondary
            font.family: Typography.sans
            font.pixelSize: Typography.meta
            font.weight: Typography.medium
        }
        Repeater {
            model: ReferenceEngines.graphOmissions
            delegate: Text {
                required property string omissionText
                Layout.fillWidth: true
                text: "–  " + omissionText
                wrapMode: Text.WordWrap
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.bodySmall
            }
        }
    }
}
