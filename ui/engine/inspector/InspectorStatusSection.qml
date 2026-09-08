import QtQuick
import "../../theme"
import "../../components"
import "../model"

/*
 * How one component currently stands in the architecture: whether the editor
 * considers it wired up, and whether it is switched into the engine at all.
 *
 * Both lines are editor state. Neither says anything about whether the
 * component would work - that judgement needs physics this build does not have.
 */
InspectorSection {
    id: root

    property string nodeId: ""
    property bool editable: true

    readonly property var node: {
        EngineModel.graphRevision
        return EngineModel.node(nodeId)
    }
    readonly property string status: {
        EngineModel.graphRevision
        return EngineModel.nodeStatus(nodeId)
    }

    title: "Status"

    InspectorRow {
        label: "Connections"
        value: root.status === "configured" ? "Complete"
             : root.status === "problem" ? "Incomplete"
             : root.status === "disabled" ? "Disabled" : "Partial"
        highlighted: root.status === "problem"
    }

    InspectorRow {
        label: "In architecture"
        visible: !root.editable
        value: root.node && root.node.enabled ? "Enabled" : "Excluded"
    }

    Item {
        width: 1
        height: root.editable ? Metrics.spacing.xs : 0
        visible: root.editable
    }

    RFToggle {
        id: enableToggle
        visible: root.editable
        text: "Enabled in architecture"
        onToggled: EngineModel.setNodeEnabled(root.nodeId, checked)
    }

    // A click writes `checked` directly, which would destroy a plain binding;
    // a Binding element re-asserts the model value instead.
    Binding {
        target: enableToggle
        property: "checked"
        value: root.node ? root.node.enabled : true
        restoreMode: Binding.RestoreNone
    }
}
