import QtQuick
import QtQuick.Controls
import "../theme"
import "../components"
import "model"

/*
 * Structural issues with the drawing, not with the engineering. Every entry
 * here comes from a rule the editor can check on its own: a required port with
 * nothing on it, a component left out of the architecture, two components
 * sharing a name.
 *
 * Selecting an entry selects and frames the component it refers to, which is
 * the interaction this panel exists to establish. The panel is reachable from
 * a component workspace, where the canvas is not on screen at all, so it asks
 * the workspace to show the architecture rather than reaching for the canvas
 * itself and quietly doing nothing.
 */
Item {
    id: root

    property Item canvas: null

    signal focusRequested(string nodeId)

    readonly property var problems: EngineModel.problems

    Flickable {
        anchors.fill: parent
        contentWidth: width
        contentHeight: column.implicitHeight
        boundsBehavior: Flickable.StopAtBounds
        clip: true

        ScrollBar.vertical: RFScrollBar {}

        Column {
            id: column
            width: parent.width

            Repeater {
                model: root.problems

                delegate: Item {
                    id: row
                    required property var modelData

                    width: column.width
                    height: 30

                    Rectangle {
                        anchors.fill: parent
                        anchors.leftMargin: Metrics.spacing.s
                        anchors.rightMargin: Metrics.spacing.s
                        radius: Metrics.radius.m
                        color: rowHover.hovered ? Theme.surface : "transparent"
                        Behavior on color { ColorAnimation { duration: Motion.fast } }
                    }

                    // Severity by shape and colour: a diamond warns, a circle informs.
                    Rectangle {
                        id: marker
                        x: Metrics.spacing.l
                        anchors.verticalCenter: parent.verticalCenter
                        width: 7
                        height: 7
                        rotation: row.modelData.severity === "warning" ? 45 : 0
                        radius: row.modelData.severity === "warning" ? 0.5 : 3.5
                        color: "transparent"
                        border.width: 1.4
                        border.color: row.modelData.severity === "warning" ? Theme.warning
                                                                           : Theme.textMuted
                    }

                    Text {
                        anchors.left: marker.right
                        anchors.leftMargin: Metrics.spacing.m
                        anchors.right: locate.left
                        anchors.rightMargin: Metrics.spacing.m
                        anchors.verticalCenter: parent.verticalCenter
                        text: row.modelData.message
                        elide: Text.ElideRight
                        color: rowHover.hovered ? Theme.text : Theme.textSecondary
                        font.family: Typography.sans
                        font.pixelSize: Typography.bodySmall
                    }

                    Text {
                        id: locate
                        anchors.right: parent.right
                        anchors.rightMargin: Metrics.spacing.l
                        anchors.verticalCenter: parent.verticalCenter
                        visible: row.modelData.targetKind === "node"
                        opacity: rowHover.hovered ? 1 : 0
                        text: "Show"
                        color: Theme.accent
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                        Behavior on opacity { NumberAnimation { duration: Motion.fast } }
                    }

                    HoverHandler {
                        id: rowHover
                        cursorShape: row.modelData.targetKind === "node" ? Qt.PointingHandCursor
                                                                        : Qt.ArrowCursor
                    }

                    TapHandler {
                        enabled: row.modelData.targetKind === "node"
                        onTapped: root.focusRequested(row.modelData.targetId)
                    }
                }
            }
        }
    }

    // ---- empty state -----------------------------------------------------

    Column {
        anchors.centerIn: parent
        visible: root.problems.length === 0
        spacing: 2

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: EngineModel.nodes.count === 0 ? "Nothing to check yet."
                                                : "No structural issues detected."
            color: Theme.textSecondary
            font.family: Typography.sans
            font.pixelSize: Typography.bodySmall
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "Editor checks only. Engineering validation needs the solver."
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
    }
}
