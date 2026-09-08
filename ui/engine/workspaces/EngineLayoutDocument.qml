import QtQuick
import "../../theme"
import "../../components"
import ".."

/*
 * The engine layout document: the toolbar and the canvas it drives. Held in
 * its own file so the workspace shell only has to know about documents, not
 * about canvases.
 */
Item {
    id: root

    property alias canvas: canvasItem

    signal componentWorkspaceRequested(string nodeId)
    signal renameRequested(string nodeId)

    EngineToolbar {
        id: toolbar
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: Metrics.spacing.m
        anchors.rightMargin: Metrics.spacing.m
        canvas: canvasItem
    }

    Rectangle {
        id: rule
        anchors.top: toolbar.bottom
        width: parent.width
        height: Metrics.hairline
        color: Theme.divider
    }

    EngineCanvas {
        id: canvasItem
        anchors.top: rule.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom

        onComponentWorkspaceRequested: function (nodeId) { root.componentWorkspaceRequested(nodeId) }
        onRenameRequested: function (nodeId) { root.renameRequested(nodeId) }
    }
}
