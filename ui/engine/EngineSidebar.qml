import QtQuick
import "../theme"
import "../components"

/*
 * The engine-mode sidebar. Two views of the same project: what exists
 * (Project) and what can be added (Components). The switch is a segmented
 * control rather than tabs, so it reads as one control rather than as a second
 * level of navigation competing with the module navigator.
 */
Item {
    id: root

    property Item canvas: null
    property Item dragLayer: null
    property int currentIndex: 0

    signal collapseRequested()

    Rectangle {
        anchors.fill: parent
        color: Theme.surfaceSubtle
        Behavior on color { ColorAnimation { duration: Motion.fast } }
    }

    RFSegmentedControl {
        id: switcher
        x: Metrics.spacing.m
        y: Metrics.spacing.m
        width: parent.width - Metrics.spacing.m * 2
                - collapseButton.width - Metrics.spacing.xs
        height: Metrics.controlHeightSmall + 2
        model: ["Project", "Components"]
        currentIndex: root.currentIndex
        onSelected: function (index) { root.currentIndex = index }
    }

    /* The fold control sits on the switcher line rather than in a header of its
     * own: a panel that has to grow a title bar in order to be closable has
     * spent more space than closing it saves. */
    RFIconButton {
        id: collapseButton
        anchors.right: parent.right
        anchors.rightMargin: Metrics.spacing.m
        anchors.verticalCenter: switcher.verticalCenter
        size: Metrics.controlHeightSmall
        iconSize: 13
        icon: "chevron-left"
        tooltip: "Hide the project panel"
        onClicked: root.collapseRequested()
    }

    Item {
        anchors.top: switcher.bottom
        anchors.topMargin: Metrics.spacing.s
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom

        EngineProjectPanel {
            anchors.fill: parent
            canvas: root.canvas
            opacity: root.currentIndex === 0 ? 1 : 0
            visible: opacity > 0
            Behavior on opacity { NumberAnimation { duration: Motion.base } }
        }

        ComponentPalette {
            anchors.fill: parent
            canvas: root.canvas
            dragLayer: root.dragLayer
            opacity: root.currentIndex === 1 ? 1 : 0
            visible: opacity > 0
            Behavior on opacity { NumberAnimation { duration: Motion.base } }
        }
    }
}
