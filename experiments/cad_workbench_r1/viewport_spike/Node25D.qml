import QtQuick
import "../../../ui/theme"
import "../../../ui/components"

/*
 * Viewport spike, Option B (2.5D): a restrained "raised card" node
 * treatment -- drop shadow + a lighter top-edge highlight -- suggesting a
 * physical component sitting on a technical drawing surface, WITHOUT
 * implying any spatial/positional relationship between nodes that is not
 * really there (the graph layout stays exactly as 2D-meaningful as the
 * accepted 2D candidate; only the node's own rendering gets a depth cue).
 * No isometric transform, no 3D projection, no real camera -- per the
 * viewport decision's own reasoning: this topology has no real dimensional
 * data, so a scene-level 3D treatment would fabricate spatial fidelity
 * the codebase does not have. Comparison-only, not wired to EngineModel.
 */
Item {
    id: node

    property string name: ""
    property string subtitle: ""
    property string glyphColor: Theme.textSecondary
    property var readout: []
    property bool selected: false

    width: 188
    height: 41 + (readout.length > 0 ? 20 + readout.length * 19 : 0)

    // Drop shadow -- a soft offset duplicate, restrained (low opacity,
    // small offset), not a glow.
    Rectangle {
        anchors.fill: parent
        anchors.topMargin: 3
        anchors.leftMargin: 1
        radius: Metrics.radius.l
        color: Theme.mode === "dark" ? "#000000" : "#00000022"
        opacity: Theme.mode === "dark" ? 0.35 : 0.12
    }

    Rectangle {
        id: surface
        anchors.fill: parent
        radius: Metrics.radius.l
        color: node.selected ? Theme.accentSubtle : Theme.surface
        border.width: node.selected ? 1.5 : Metrics.hairline
        border.color: node.selected ? Theme.accent : Theme.border
    }

    // Top-edge highlight -- a thin lighter line along the top, the depth
    // cue itself: it reads as a raised, lit-from-above panel without any
    // gradient fill, bloom, or cinematic lighting.
    Rectangle {
        anchors.top: surface.top
        anchors.left: surface.left
        anchors.right: surface.right
        anchors.topMargin: 1
        anchors.leftMargin: 1
        anchors.rightMargin: 1
        height: 1
        radius: 1
        color: Theme.mode === "dark" ? "#ffffff" : "#ffffff"
        opacity: Theme.mode === "dark" ? 0.10 : 0.55
    }

    Row {
        x: 10
        y: 0
        height: 41
        spacing: 8

        Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            width: 23
            height: 23
            radius: 4
            color: "transparent"
            border.width: 1.4
            border.color: node.glyphColor
        }

        Column {
            anchors.verticalCenter: parent.verticalCenter
            spacing: 0

            Text {
                text: node.name
                color: Theme.text
                font.family: Typography.sans
                font.pixelSize: Typography.body
                font.weight: Typography.semibold
            }
            Text {
                text: node.subtitle
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }
        }
    }

    Rectangle {
        visible: node.readout.length > 0
        y: 41
        width: parent.width
        height: Metrics.hairline
        color: Theme.divider
    }

    Column {
        visible: node.readout.length > 0
        y: 41 + 10
        x: 12
        width: parent.width - 24
        spacing: 0

        Repeater {
            model: node.readout
            delegate: Item {
                required property var modelData
                width: parent.width
                height: 19

                Text {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    text: modelData.label
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                }
                Text {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    text: modelData.value + (modelData.unit ? " " + modelData.unit : "")
                    color: modelData.value === "—" ? Theme.textDisabled : Theme.text
                    font.family: Typography.mono
                    font.pixelSize: Typography.readoutSmall
                }
            }
        }
    }
}
