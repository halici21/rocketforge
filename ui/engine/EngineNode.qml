import QtQuick
import "../theme"
import "../components"
import "model"
import "visuals"

/*
 * EngineNode - one physical component on the canvas.
 *
 * There is a single node implementation rather than one file per component
 * type: everything that differs between a tank and a turbine (glyph, ports,
 * placeholder rows, size) is registry data. Adding a component type is a
 * registry entry, not a new QML file, which is what lets the palette grow to
 * the twenty or thirty parts a real engine model needs.
 *
 * A node shows only enough to identify the component and its state. Numbers
 * that matter belong in the inspector and in the component workspace, so the
 * canvas stays readable at forty components.
 *
 * Two densities. In `normal` the component name is the loudest thing on the
 * node and the placeholder rows sit under it; in `compact` the node falls back
 * to the identity strip alone. Only the name and the glyph are held at full
 * strength in both - everything else is what gives way first.
 */
Item {
    id: node

    property Item canvas: null
    property string nodeId: ""
    property string type: ""
    property string name: ""
    property var meta: null
    property bool nodeEnabled: true

    readonly property var definition: ComponentRegistry.definition(type)
    readonly property var geometry: ComponentRegistry.nodeSize(type, EngineModel.detailLevel)
    readonly property bool compact: EngineModel.detailLevel === "compact"

    readonly property bool selected: {
        EngineModel.selectedNodes
        return EngineModel.isNodeSelected(nodeId)
    }
    readonly property string status: {
        EngineModel.graphRevision
        return EngineModel.nodeStatus(nodeId)
    }
    readonly property var readout: meta && meta.readout ? meta.readout : []

    width: geometry.width
    height: geometry.height
    opacity: nodeEnabled ? 1 : 0.45

    Behavior on opacity { NumberAnimation { duration: Motion.base } }

    // ---- surface ---------------------------------------------------------

    Rectangle {
        id: surface
        anchors.fill: parent
        radius: Metrics.radius.l
        color: node.selected ? Theme.accentSubtle
             : hover.hovered ? Theme.surfaceElevated
             : Theme.surface
        border.width: node.selected ? 1.5 : Metrics.hairline
        border.color: node.selected ? Theme.accent
                    : hover.hovered ? Theme.borderStrong
                    : Theme.border

        Behavior on color { ColorAnimation { duration: Motion.fast } }
        Behavior on border.color { ColorAnimation { duration: Motion.fast } }
    }

    // ---- header ----------------------------------------------------------

    Item {
        id: header
        width: parent.width
        height: ComponentRegistry.headerHeightFor(EngineModel.detailLevel)

        ComponentGlyph {
            id: glyph
            x: Metrics.spacing.m - 2
            anchors.verticalCenter: parent.verticalCenter
            width: node.compact ? 19 : 23
            height: width
            glyph: node.definition ? node.definition.glyph : ""
            color: node.selected ? Theme.accent
                 : node.nodeEnabled ? Theme.textSecondary : Theme.textDisabled
        }

        Column {
            anchors.left: glyph.right
            anchors.leftMargin: Metrics.spacing.s
            anchors.right: statusMark.left
            anchors.rightMargin: Metrics.spacing.s
            anchors.verticalCenter: parent.verticalCenter
            spacing: 0

            Text {
                width: parent.width
                text: node.name
                elide: Text.ElideRight
                color: node.nodeEnabled ? Theme.text : Theme.textDisabled
                font.family: Typography.sans
                // The name is the one thing that must survive at any density.
                font.pixelSize: node.compact ? Typography.bodySmall : Typography.body
                font.weight: node.compact ? Typography.medium : Typography.semibold
            }

            Text {
                width: parent.width
                visible: !node.compact && node.meta && node.meta.subtitle
                text: node.meta ? node.meta.subtitle : ""
                elide: Text.ElideRight
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }
        }

        // Status marker: shape and colour, never colour alone.
        Item {
            id: statusMark
            anchors.right: parent.right
            anchors.rightMargin: Metrics.spacing.m - 2
            anchors.verticalCenter: parent.verticalCenter
            width: 9
            height: 9

            Rectangle {
                anchors.centerIn: parent
                width: node.status === "disabled" ? 9 : 8
                height: node.status === "disabled" ? 2 : 8
                rotation: node.status === "problem" ? 45 : 0
                radius: node.status === "configured" || node.status === "unconfigured" ? width / 2 : 0.5
                color: node.status === "configured" ? Theme.success
                     : node.status === "problem" ? Theme.warning
                     : node.status === "disabled" ? Theme.textDisabled
                     : "transparent"
                border.width: node.status === "unconfigured" ? 1.4 : 0
                border.color: Theme.textMuted

                Behavior on color { ColorAnimation { duration: Motion.base } }
            }

            HoverHandler { id: statusHover }
            RFTooltip {
                text: node.status === "configured" ? "All ports connected"
                    : node.status === "problem" ? "A required port is unconnected"
                    : node.status === "disabled" ? "Component disabled"
                    : "Not fully connected"
                visible: statusHover.hovered
                x: -width + parent.width
                y: parent.height + 4
            }
        }
    }

    // ---- placeholder readout --------------------------------------------

    Rectangle {
        id: headerRule
        visible: !node.compact && node.readout.length > 0
        y: header.height
        width: parent.width
        height: Metrics.hairline
        color: node.selected ? Theme.accent : Theme.divider
        opacity: node.selected ? 0.35 : 1
    }

    Column {
        visible: !node.compact
        y: header.height + ComponentRegistry.bodyPadding
        x: Metrics.spacing.m
        width: parent.width - Metrics.spacing.m * 2
        spacing: 0

        Repeater {
            model: node.readout

            delegate: Item {
                required property var modelData
                width: parent.width
                height: ComponentRegistry.rowHeight

                Text {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    text: modelData.label
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                }

                Row {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 3

                    Text {
                        text: modelData.value
                        color: modelData.value === "—" ? Theme.textDisabled : Theme.text
                        font.family: Typography.mono
                        font.pixelSize: Typography.readoutSmall
                    }
                    Text {
                        visible: modelData.unit !== ""
                        text: modelData.unit
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                }
            }
        }
    }

    // ---- ports -----------------------------------------------------------

    Repeater {
        model: node.definition ? node.definition.ports : []

        delegate: EnginePort {
            required property var modelData

            readonly property var offset: ComponentRegistry.portOffset(
                                              node.type, modelData.id, EngineModel.detailLevel)

            canvas: node.canvas
            nodeId: node.nodeId
            portSpec: modelData
            x: offset.x - width / 2
            y: offset.y - height / 2
        }
    }

    // ---- interaction -----------------------------------------------------

    HoverHandler {
        id: hover
        cursorShape: Qt.OpenHandCursor
    }

    TapHandler {
        acceptedButtons: Qt.LeftButton
        onTapped: function (point, button) {
            EngineModel.selectNode(node.nodeId, point.modifiers & Qt.ShiftModifier)
        }
        onDoubleTapped: {
            if (node.canvas)
                node.canvas.openComponentWorkspace(node.nodeId)
        }
    }

    TapHandler {
        acceptedButtons: Qt.RightButton
        onTapped: function (point) {
            if (!EngineModel.isNodeSelected(node.nodeId))
                EngineModel.selectNode(node.nodeId, false)
            if (node.canvas)
                node.canvas.requestNodeMenu(node.nodeId, node.mapToItem(node.canvas, point.position))
        }
    }

    DragHandler {
        id: dragHandler
        target: null
        property var origins: ({})

        onActiveChanged: {
            if (active) {
                if (!EngineModel.isNodeSelected(node.nodeId))
                    EngineModel.selectNode(node.nodeId, false)
                origins = {}
                var ids = EngineModel.selectedNodes
                for (var i = 0; i < ids.length; ++i) {
                    var n = EngineModel.node(ids[i])
                    if (n)
                        origins[ids[i]] = { x: n.x, y: n.y }
                }
            }
        }

        onActiveTranslationChanged: {
            if (!active)
                return
            for (var id in origins) {
                var start = origins[id]
                node.canvas.placeNode(id,
                                      start.x + activeTranslation.x,
                                      start.y + activeTranslation.y)
            }
        }
    }
}
