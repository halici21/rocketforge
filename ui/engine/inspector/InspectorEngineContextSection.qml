import QtQuick
import "../../theme"
import "../../components"
import "../model"

/*
 * The project a component belongs to. Shown inside a component workspace,
 * where the surrounding engine has gone off screen and the user is one tab
 * removed from the thing that gives the numbers their meaning.
 */
InspectorSection {
    id: root

    property string nodeId: ""

    readonly property var node: {
        EngineModel.graphRevision
        return EngineModel.node(nodeId)
    }
    readonly property var definition: node ? ComponentRegistry.definition(node.type) : null

    title: "Project"

    InspectorRow { label: "Engine"; value: EngineModel.engineName }
    InspectorRow { label: "Cycle"; value: EngineModel.architecture }
    InspectorRow { label: "Propellants"; value: EngineModel.propellants }
    InspectorRow {
        label: "Subsystem"
        value: root.definition ? ComponentRegistry.subsystemLabel(root.definition.category) : "—"
    }
}
