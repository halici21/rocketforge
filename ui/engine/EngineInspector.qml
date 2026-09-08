import QtQuick
import QtQuick.Controls
import "../theme"
import "../components"
import "model"
import "inspector"

/*
 * The context panel.
 *
 * One inspector, several states, chosen from two inputs rather than one: what
 * is selected, and *where the user is standing while selecting it*. The second
 * input is what stops the panel from offering to open the workspace that is
 * already on screen. Selection alone cannot tell those two situations apart -
 * the injector is selected in both - so the workspace tells the inspector which
 * document is open and the panel decides accordingly:
 *
 *     engine layout,     nothing selected  ->  the engine
 *     engine layout,     one component     ->  component + way into its workspace
 *     engine layout,     one connection    ->  the connection
 *     engine layout,     several           ->  the selection
 *     component workspace, its own part    ->  engine context around it
 *     component workspace, another part    ->  that component, workspace offered
 *
 * The last two lines are the point. Inside the injector workspace the panel
 * describes the engine around the injector; but if the user reaches over to the
 * project tree and picks the fuel pump, offering to open the *pump* workspace
 * is navigation, not repetition, so it comes back.
 *
 * Every selection source - canvas, project tree, problems list - writes to the
 * same place in EngineModel, so this panel never has to know where a selection
 * came from.
 */
Item {
    id: root

    // Where the user currently is. Written by the workspace shell.
    property string contextKind: "layout"      // layout | component
    property string contextNodeId: ""

    signal componentWorkspaceRequested(string nodeId)
    signal engineLayoutRequested(string nodeId)
    signal collapseRequested()
    signal newEngineRequested()
    signal demoRequested()

    readonly property string inspectorMode: {
        EngineModel.selectedNodes            // dependency: re-evaluate on selection
        if (EngineModel.selectionKind === "connection")
            return "connection"

        var insideComponent = contextKind === "component" && contextNodeId !== ""
        if (insideComponent) {
            var elsewhere = EngineModel.selectionKind === "node"
                            && !EngineModel.isNodeSelected(contextNodeId)
            if (!elsewhere)
                return "componentContext"
        }

        if (EngineModel.selectionKind === "node")
            return EngineModel.selectedNodes.length > 1 ? "multi" : "node"
        return insideComponent ? "componentContext" : "engine"
    }

    /* Rename arrives from a context menu, and a closing popup hands focus back
     * as it finishes its exit transition. Wait for that, or the field takes
     * focus and immediately loses it again. */
    function focusName() {
        renameFocus.restart()
    }

    Timer {
        id: renameFocus
        interval: Motion.base + 40
        onTriggered: {
            if (content.item && content.item.focusName)
                content.item.focusName()
        }
    }

    Rectangle {
        anchors.fill: parent
        color: Theme.surfaceSubtle
        Behavior on color { ColorAnimation { duration: Motion.fast } }
    }

    /* Folding the inspector away is offered from inside it, on the same line
     * the content starts on, so the panel needs no chrome of its own to be
     * dismissible. */
    RFIconButton {
        id: collapseButton
        anchors.right: parent.right
        anchors.rightMargin: Metrics.spacing.s
        anchors.top: parent.top
        anchors.topMargin: Metrics.spacing.s
        z: 2
        size: 24
        iconSize: 13
        icon: "chevron-right"
        tooltip: "Hide the inspector"
        onClicked: root.collapseRequested()
    }

    Flickable {
        anchors.fill: parent
        contentWidth: width
        contentHeight: content.height + Metrics.spacing.xl * 2
        boundsBehavior: Flickable.StopAtBounds
        clip: true

        ScrollBar.vertical: RFScrollBar {}

        Loader {
            id: content
            x: Metrics.spacing.l
            y: Metrics.spacing.xl
            // Clear of the fold control, which floats over this column.
            width: parent.width - Metrics.spacing.l - Metrics.spacing.s
                   - collapseButton.width

            sourceComponent: root.inspectorMode === "connection" ? connectionView
                           : root.inspectorMode === "multi" ? multiView
                           : root.inspectorMode === "componentContext" ? componentContextView
                           : root.inspectorMode === "node" ? nodeView
                           : engineView

            onItemChanged: fade.restart()

            NumberAnimation {
                id: fade
                target: content
                property: "opacity"
                from: 0
                to: 1
                duration: Motion.base
                easing.type: Motion.standard
            }
        }
    }

    // ---- states ----------------------------------------------------------

    Component {
        id: engineView
        EngineOverviewInspector { inspector: root }
    }

    Component {
        id: nodeView
        NodeInspector {
            inspector: root
            nodeId: EngineModel.selectionId
            // Only offer the workspace of a component whose workspace is not
            // the page this panel is sitting beside.
            showNavigation: root.contextNodeId !== EngineModel.selectionId
        }
    }

    Component {
        id: componentContextView
        ComponentContextInspector {
            inspector: root
            nodeId: root.contextNodeId
        }
    }

    Component {
        id: connectionView
        ConnectionInspector {
            inspector: root
            connId: EngineModel.selectionId
        }
    }

    Component {
        id: multiView

        Column {
            width: parent ? parent.width : 0
            spacing: Metrics.spacing.xl

            Column {
                width: parent.width
                spacing: Metrics.spacing.s

                Text {
                    text: EngineModel.selectedNodes.length + " components selected"
                    color: Theme.text
                    font.family: Typography.sans
                    font.pixelSize: Typography.groupLabel + 3
                    font.weight: Typography.semibold
                }
                Text {
                    width: parent.width
                    text: "Move them together on the canvas, or act on the whole selection."
                    wrapMode: Text.WordWrap
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                }
            }

            InspectorSection {
                title: "Selection"

                Repeater {
                    model: EngineModel.selectedNodes

                    delegate: InspectorRow {
                        required property var modelData
                        label: ComponentRegistry.displayName(
                                   EngineModel.node(modelData) ? EngineModel.node(modelData).type : "")
                        value: EngineModel.nodeName(modelData)
                        interactive: true
                        onActivated: EngineModel.selectNode(modelData, false)
                    }
                }
            }

            Column {
                width: parent.width
                spacing: Metrics.spacing.s

                RFButton {
                    width: parent.width
                    text: "Duplicate selection"
                    compact: true
                    onClicked: EngineModel.duplicateSelection()
                }
                RFButton {
                    width: parent.width
                    text: "Delete selection"
                    variant: "quiet"
                    compact: true
                    onClicked: EngineModel.deleteSelection()
                }
            }
        }
    }
}
