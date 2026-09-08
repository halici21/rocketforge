import QtQuick
import "../../theme"
import "../../components"
import "../model"

/*
 * What the inspector shows when nothing is selected: the engine itself. An
 * empty properties panel would waste the most valuable column on screen.
 */
Column {
    id: root

    property Item inspector: null

    readonly property int componentCount: EngineModel.nodes.count
    readonly property int connectionCount: EngineModel.connections.count
    readonly property int problemCount: EngineModel.problems.length

    width: parent ? parent.width : 0
    spacing: Metrics.spacing.xl

    // ---- header ----------------------------------------------------------

    Column {
        width: parent.width
        spacing: Metrics.spacing.s

        Text {
            width: parent.width
            text: EngineModel.engineName
            elide: Text.ElideRight
            color: Theme.text
            font.family: Typography.sans
            font.pixelSize: Typography.groupLabel + 3
            font.weight: Typography.semibold
        }

        RFStatusChip {
            text: root.componentCount === 0 ? "Empty" : MockEngineData.configurationState
            tone: root.componentCount === 0 ? "neutral" : "warning"
        }
    }

    // ---- architecture ----------------------------------------------------

    InspectorSection {
        title: "Architecture"

        InspectorRow { label: "Cycle"; value: EngineModel.architecture }
        InspectorRow { label: "Propellants"; value: EngineModel.propellants }
        InspectorRow { label: "Environment"; value: EngineModel.environment }
    }

    InspectorSection {
        title: "Contents"

        InspectorRow { label: "Components"; value: root.componentCount + ""; numeric: true }
        InspectorRow { label: "Connections"; value: root.connectionCount + ""; numeric: true }
        InspectorRow {
            label: "Structural issues"
            value: root.problemCount + ""
            numeric: true
            highlighted: root.problemCount > 0
        }
    }

    InspectorSection {
        title: "Performance"

        InspectorRow { label: "Thrust"; value: "—"; numeric: true }
        InspectorRow { label: "Chamber pressure"; value: "—"; numeric: true }
        InspectorRow { label: "Mixture ratio"; value: "—"; numeric: true }

        Text {
            width: parent.width
            text: "Engine performance needs the solver. These rows exist to show where it "
                  + "will appear, and stay empty until then."
            wrapMode: Text.WordWrap
            lineHeight: Typography.proseLineHeight
            lineHeightMode: Text.ProportionalHeight
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
    }

    // ---- actions ---------------------------------------------------------

    Column {
        width: parent.width
        spacing: Metrics.spacing.s

        RFButton {
            width: parent.width
            text: "New engine…"
            compact: true
            onClicked: { if (root.inspector) root.inspector.newEngineRequested() }
        }

        RFButton {
            width: parent.width
            text: EngineModel.nodes.count > 0 ? "Reload demo engine" : "Load demo engine"
            variant: "quiet"
            compact: true
            onClicked: { if (root.inspector) root.inspector.demoRequested() }
        }
    }
}
