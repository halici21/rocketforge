import QtQuick
import "../../theme"
import "../../components"
import "../model"

/*
 * The inspector for one component seen from the engine layout: what it is, what
 * it is called, what it is joined to, and the way into its detailed workspace.
 *
 * It is metadata and navigation, not a design page - the numbers that will
 * eventually need a solver stay in the component workspace where there is room
 * for them.
 *
 * `showNavigation` is the whole reason this file and ComponentContextInspector
 * are separate states rather than one panel with a hidden button: the workspace
 * decides whether opening a workspace is a sensible thing to offer, and the
 * inspector does not have to guess.
 */
Column {
    id: root

    property Item inspector: null
    property string nodeId: ""
    property bool showNavigation: true

    readonly property var node: {
        EngineModel.graphRevision
        return EngineModel.node(nodeId)
    }
    readonly property var definition: node ? ComponentRegistry.definition(node.type) : null
    readonly property string status: {
        EngineModel.graphRevision
        return EngineModel.nodeStatus(nodeId)
    }

    function focusName() {
        nameField.focusInput()
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

    // ---- general ---------------------------------------------------------

    InspectorSection {
        title: "General"

        RFTextField {
            id: nameField
            width: parent.width
            label: "Name"
            text: root.node ? root.node.name : ""
            onEdited: EngineModel.renameNode(root.nodeId, text)
        }

        Item { width: 1; height: Metrics.spacing.xs }

        InspectorRow {
            label: "Component type"
            value: root.definition ? root.definition.displayName : ""
        }
        InspectorRow {
            label: "Model"
            value: root.node && root.node.meta ? root.node.meta.subtitle : ""
        }

        Item { width: 1; height: Metrics.spacing.xs }

        RFToggle {
            id: enableToggle
            text: "Enabled in architecture"
            onToggled: EngineModel.setNodeEnabled(root.nodeId, checked)
        }

        // A click writes `checked` directly, which would destroy a plain
        // binding; a Binding element re-asserts the model value instead.
        Binding {
            target: enableToggle
            property: "checked"
            value: root.node ? root.node.enabled : true
            restoreMode: Binding.RestoreNone
        }
    }

    // ---- design ----------------------------------------------------------

    InspectorNavigationSection {
        title: "Design"
        visible: root.showNavigation
        label: "Open " + (root.definition ? root.definition.displayName.toLowerCase() : "")
               + " workspace"
        description: root.definition && root.definition.workspace === "placeholder"
                     ? "This component's workspace is a reserved frame in this build."
                     : "Opens as a workspace tab alongside the engine layout."
        onActivated: {
            if (root.inspector)
                root.inspector.componentWorkspaceRequested(root.nodeId)
        }
    }

    // ---- connections -----------------------------------------------------

    InspectorConnectionsSection {
        nodeId: root.nodeId
    }

    // ---- placeholder values ---------------------------------------------

    InspectorSection {
        title: "Configuration"
        visible: root.node && root.node.meta && root.node.meta.readout.length > 0

        Repeater {
            model: root.node && root.node.meta ? root.node.meta.readout : []

            delegate: InspectorRow {
                required property var modelData
                label: modelData.label
                value: modelData.value + (modelData.unit ? " " + modelData.unit : "")
                numeric: true
            }
        }

        Text {
            width: parent.width
            text: "Placeholder values. Component configuration and solving arrive with the "
                  + "engineering modules."
            wrapMode: Text.WordWrap
            lineHeight: Typography.proseLineHeight
            lineHeightMode: Text.ProportionalHeight
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
    }
}
