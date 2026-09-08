import QtQuick
import "../../theme"
import "../../components"
import "../model"

/*
 * The inspector while the user is already standing inside a component's own
 * workspace.
 *
 * The panel changes job here. On the engine layout the inspector describes a
 * part and offers the way into it; once that way has been taken, repeating the
 * offer is the single most obvious piece of dead weight in the interface - the
 * button opens the page it is drawn on. So the panel stops describing the
 * component, which the workspace is already doing at full size, and starts
 * describing the engine around it: what it is fed by, what it feeds, and which
 * project it belongs to. That is the context the workspace cannot show, because
 * the canvas is one tab away.
 *
 * Configuration stays in the workspace, context stays here, and the two do not
 * duplicate each other.
 */
Column {
    id: root

    property Item inspector: null
    property string nodeId: ""

    readonly property var node: {
        EngineModel.graphRevision
        return EngineModel.node(nodeId)
    }
    readonly property var definition: node ? ComponentRegistry.definition(node.type) : null
    readonly property string status: {
        EngineModel.graphRevision
        return EngineModel.nodeStatus(nodeId)
    }

    width: parent ? parent.width : 0
    spacing: Metrics.spacing.xl

    InspectorHeader {
        title: root.node ? root.node.name : ""
        glyph: root.definition ? root.definition.glyph : ""

        RFStatusChip {
            text: root.definition ? root.definition.displayName : ""
            showDot: false
        }
        RFStatusChip {
            text: root.status === "configured" ? "Connected"
                : root.status === "problem" ? "Incomplete"
                : root.status === "disabled" ? "Disabled" : "Partial"
            tone: root.status === "configured" ? "success"
                : root.status === "problem" ? "warning" : "neutral"
        }
    }

    InspectorStatusSection {
        nodeId: root.nodeId
        editable: true
    }

    // The engine around the component, which is what has gone off screen.
    InspectorConnectionsSection {
        nodeId: root.nodeId
        title: "Engine context"
        // The canvas is not on screen, so there is nothing for a selected
        // connection to reveal.
        selectable: false
        emptyNote: "This component is not joined to the architecture."
    }

    InspectorEngineContextSection {
        nodeId: root.nodeId
    }

    InspectorNavigationSection {
        title: ""
        label: "Show in engine layout"
        icon: "chevron-left"
        description: "Returns to the architecture with this component selected."
        onActivated: {
            if (root.inspector)
                root.inspector.engineLayoutRequested(root.nodeId)
        }
    }

    InspectorSection {
        title: "Notes"

        Text {
            width: parent.width
            text: "Every quantity in this workspace is a placeholder. Component "
                  + "configuration is stored, but nothing is evaluated until the "
                  + "engineering module for this component exists."
            wrapMode: Text.WordWrap
            lineHeight: Typography.proseLineHeight
            lineHeightMode: Text.ProportionalHeight
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
    }
}
