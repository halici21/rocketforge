import QtQuick
import "../../theme"
import "../../components"
import "../model"

/*
 * What one component is joined to, port by port.
 *
 * The same list answers two different questions depending on where it is shown.
 * On the engine layout it is "what is wired to this part"; inside a component
 * workspace it is "where does this part sit in the engine" - which is the one
 * piece of context the workspace itself cannot show, because the canvas is not
 * on screen. Same data, so it is one component.
 */
InspectorSection {
    id: root

    property string nodeId: ""
    // Selecting a connection is only useful where the canvas can show it.
    property bool selectable: true
    property string emptyNote: "This component has no ports."

    readonly property var portRows: {
        EngineModel.graphRevision
        var node = EngineModel.node(nodeId)
        if (!node)
            return []
        var ports = ComponentRegistry.ports(node.type)
        var rows = []
        for (var i = 0; i < ports.length; ++i) {
            var conn = EngineModel.connectionForPort(nodeId, ports[i].id)
            var peer = ""
            if (conn)
                peer = conn.fromNode === nodeId ? conn.toNode : conn.fromNode
            rows.push({
                label: ports[i].label,
                required: ports[i].required === true,
                peer: peer ? EngineModel.nodeName(peer) : "—",
                connId: conn ? conn.connId : ""
            })
        }
        return rows
    }

    title: "Connections"

    Repeater {
        model: root.portRows

        delegate: InspectorRow {
            required property var modelData
            label: modelData.label
            value: modelData.peer
            interactive: root.selectable && modelData.connId !== ""
            highlighted: modelData.connId !== ""
            onActivated: EngineModel.selectConnection(modelData.connId)
        }
    }

    Text {
        width: parent.width
        visible: root.portRows.length === 0
        text: root.emptyNote
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.meta
    }
}
