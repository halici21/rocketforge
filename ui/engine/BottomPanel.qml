import QtQuick
import "../theme"
import "../components"
import "model"

/*
 * The collapsible engineering panel. Collapsed to a single row by default -
 * the canvas is the work, and this is where the workspace answers back.
 */
Item {
    id: root

    property Item canvas: null
    property bool expanded: false
    property int currentTab: 0

    // A problem refers to something that only exists on the canvas, so acting
    // on one has to be able to put the canvas back on screen.
    signal focusRequested(string nodeId)
    readonly property real collapsedHeight: 32
    readonly property real expandedHeight: 176

    readonly property int problemCount: EngineModel.problems.length

    function open(tabIndex) {
        currentTab = tabIndex
        expanded = true
    }

    implicitHeight: expanded ? expandedHeight : collapsedHeight

    Behavior on implicitHeight {
        NumberAnimation { duration: Motion.base; easing.type: Motion.emphasized }
    }

    Rectangle {
        anchors.fill: parent
        color: Theme.surfaceSubtle
        Behavior on color { ColorAnimation { duration: Motion.fast } }
    }

    Rectangle {
        width: parent.width
        height: Metrics.hairline
        color: Theme.divider
    }

    // ---- tab strip -------------------------------------------------------

    Item {
        id: strip
        width: parent.width
        height: root.collapsedHeight

        Row {
            anchors.left: parent.left
            anchors.leftMargin: Metrics.spacing.m
            anchors.verticalCenter: parent.verticalCenter
            spacing: Metrics.spacing.xs

            Repeater {
                model: [
                    { label: "Problems", available: true },
                    { label: "Results", available: false },
                    { label: "Messages", available: true }
                ]

                delegate: Item {
                    id: tab
                    required property var modelData
                    required property int index

                    readonly property bool current: root.expanded && root.currentTab === index

                    width: tabLabel.implicitWidth + badge.width + Metrics.spacing.m
                    height: root.collapsedHeight - 6
                    anchors.verticalCenter: parent.verticalCenter

                    Rectangle {
                        anchors.fill: parent
                        radius: Metrics.radius.m
                        color: tab.current ? Theme.surface
                             : tabHover.hovered && tab.modelData.available ? Theme.surfaceHover
                             : "transparent"
                        Behavior on color { ColorAnimation { duration: Motion.fast } }
                    }

                    Row {
                        anchors.centerIn: parent
                        spacing: Metrics.spacing.xs

                        Text {
                            id: tabLabel
                            anchors.verticalCenter: parent.verticalCenter
                            text: tab.modelData.label
                            color: !tab.modelData.available ? Theme.textDisabled
                                 : tab.current ? Theme.text : Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.bodySmall
                            font.weight: tab.current ? Typography.medium : Typography.regular
                            Behavior on color { ColorAnimation { duration: Motion.fast } }
                        }

                        Rectangle {
                            id: badge
                            anchors.verticalCenter: parent.verticalCenter
                            visible: tab.index === 0 && root.problemCount > 0
                            width: visible ? countText.implicitWidth + 10 : 0
                            height: 15
                            radius: Metrics.radius.xs
                            color: Theme.surfaceSunken
                            border.width: Metrics.hairline
                            border.color: Theme.divider

                            Text {
                                id: countText
                                anchors.centerIn: parent
                                text: root.problemCount
                                color: Theme.warning
                                font.family: Typography.mono
                                font.pixelSize: Typography.meta
                            }
                        }
                    }

                    HoverHandler {
                        id: tabHover
                        cursorShape: tab.modelData.available ? Qt.PointingHandCursor : Qt.ArrowCursor
                    }

                    TapHandler {
                        enabled: tab.modelData.available
                        onTapped: {
                            if (root.expanded && root.currentTab === tab.index)
                                root.expanded = false
                            else
                                root.open(tab.index)
                        }
                    }

                    RFTooltip {
                        text: "Available after solver implementation"
                        visible: !tab.modelData.available && tabHover.hovered
                        x: 0
                        y: -height - 6
                    }
                }
            }
        }

        RFIconButton {
            anchors.right: parent.right
            anchors.rightMargin: Metrics.spacing.m
            anchors.verticalCenter: parent.verticalCenter
            size: 22
            iconSize: 13
            icon: "chevron-down"
            rotation: root.expanded ? 0 : 180
            tooltip: root.expanded ? "Collapse panel" : "Expand panel"
            onClicked: root.expanded = !root.expanded

            Behavior on rotation {
                NumberAnimation { duration: Motion.base; easing.type: Motion.standard }
            }
        }
    }

    // ---- content ---------------------------------------------------------

    Item {
        anchors.top: strip.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        clip: true
        opacity: root.expanded ? 1 : 0
        visible: opacity > 0

        Behavior on opacity { NumberAnimation { duration: Motion.fast } }

        Rectangle {
            width: parent.width
            height: Metrics.hairline
            color: Theme.divider
        }

        ProblemsPanel {
            anchors.fill: parent
            anchors.topMargin: Metrics.spacing.xs
            visible: root.currentTab === 0
            canvas: root.canvas
            onFocusRequested: function (nodeId) { root.focusRequested(nodeId) }
        }

        // Results: deliberately empty until a solver exists.
        Column {
            anchors.centerIn: parent
            visible: root.currentTab === 1
            spacing: 2

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "No results"
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.bodySmall
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "Available after solver implementation."
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }
        }

        Column {
            visible: root.currentTab === 2
            x: Metrics.spacing.l
            y: Metrics.spacing.m
            width: parent.width - Metrics.spacing.l * 2
            spacing: Metrics.spacing.s

            Repeater {
                model: [
                    "Engine workspace running in UI preview mode.",
                    "Component library loaded from the registry: "
                        + ComponentRegistry.types.length + " component types.",
                    "No solver is present in this build; all component values are placeholders."
                ]

                delegate: Row {
                    required property var modelData
                    spacing: Metrics.spacing.m

                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "·"
                        color: Theme.textDisabled
                        font.family: Typography.sans
                        font.pixelSize: Typography.bodySmall
                    }
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: modelData
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.bodySmall
                    }
                }
            }
        }
    }
}
