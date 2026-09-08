import QtQuick
import "../../theme"
import "../../components"
import "../model"

/*
 * The inspector for one connection. A connection is a first-class object here
 * because it is where the solver will eventually put mass flow, pressure and
 * temperature; today it carries only its endpoints and its type.
 */
Column {
    id: root

    property Item inspector: null
    property string connId: ""

    readonly property var link: {
        EngineModel.graphRevision
        return EngineModel.connection(connId)
    }
    readonly property var sourcePort: link ? ComponentRegistry.port(
                                                 EngineModel.node(link.fromNode).type,
                                                 link.fromPort) : null
    readonly property var targetPort: link ? ComponentRegistry.port(
                                                 EngineModel.node(link.toNode).type,
                                                 link.toPort) : null

    width: parent ? parent.width : 0
    spacing: Metrics.spacing.xl

    // ---- header ----------------------------------------------------------

    Column {
        width: parent.width
        spacing: Metrics.spacing.s

        Text {
            width: parent.width
            text: root.link ? root.link.name : ""
            elide: Text.ElideRight
            color: Theme.text
            font.family: Typography.sans
            font.pixelSize: Typography.groupLabel + 3
            font.weight: Typography.semibold
        }

        Row {
            spacing: Metrics.spacing.s

            RFStatusChip {
                text: root.link ? ComponentRegistry.portTypeLabel(root.link.portType) : ""
                showDot: false
            }
            RFStatusChip {
                text: "Not solved"
                tone: "neutral"
            }
        }
    }

    // ---- general ---------------------------------------------------------

    InspectorSection {
        title: "General"

        InspectorRow {
            label: "Port type"
            value: root.link ? ComponentRegistry.portTypeLabel(root.link.portType) : ""
        }
        InspectorRow {
            label: "Medium"
            value: root.link ? root.link.subtype : ""
        }
    }

    // ---- endpoints -------------------------------------------------------

    InspectorSection {
        title: "From"

        InspectorRow {
            label: "Component"
            value: root.link ? EngineModel.nodeName(root.link.fromNode) : ""
            interactive: true
            highlighted: true
            onActivated: EngineModel.selectNode(root.link.fromNode, false)
        }
        InspectorRow {
            label: "Port"
            value: root.sourcePort ? root.sourcePort.label : ""
        }
    }

    InspectorSection {
        title: "To"

        InspectorRow {
            label: "Component"
            value: root.link ? EngineModel.nodeName(root.link.toNode) : ""
            interactive: true
            highlighted: true
            onActivated: EngineModel.selectNode(root.link.toNode, false)
        }
        InspectorRow {
            label: "Port"
            value: root.targetPort ? root.targetPort.label : ""
        }
    }

    // ---- state -----------------------------------------------------------

    InspectorSection {
        title: "State"

        InspectorRow { label: "Mass flow"; value: "—"; numeric: true }
        InspectorRow { label: "Pressure"; value: "—"; numeric: true }
        InspectorRow { label: "Temperature"; value: "—"; numeric: true }

        Text {
            width: parent.width
            text: "A connection will carry state once a solver exists. Nothing is transported "
                  + "along it in this build."
            wrapMode: Text.WordWrap
            lineHeight: Typography.proseLineHeight
            lineHeightMode: Text.ProportionalHeight
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
    }

    // ---- actions ---------------------------------------------------------

    RFButton {
        width: parent.width
        text: "Delete connection"
        variant: "quiet"
        compact: true
        onClicked: EngineModel.removeConnection(root.connId)
    }
}
