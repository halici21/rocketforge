import QtQuick
import QtQuick.Layouts
import "../theme"
import "../components"

/*
 * The Analysis Dock -- collapsible AND resizable, along the bottom of
 * Analysis mode's workspace region.
 *
 * Chrome only: this component owns the tab strip, the collapse/expand
 * chevron and the drag-to-resize handle. What each tab actually shows is
 * the caller's decision (default property `content`), because what belongs
 * in a workspace's dock is a per-workspace question (brief section 45),
 * not something this shell primitive should decide for every page.
 *
 * Collapsed to a single strip by default, mirroring
 * ui/engine/BottomPanel.qml's own rule: "the canvas is the work, and this
 * is where the workspace answers back." A dock that opens itself steals
 * vertical room from the engineering object it is supposed to support.
 *
 * Resizing is a direct drag on `expandedHeight`, not a SplitView. Engine
 * Design's own dock (BottomPanel.qml) is a plain animated-height row below
 * the horizontal SplitView, not a SplitView child itself -- there is no
 * existing vertical-SplitView pattern in this codebase to extend, and
 * introducing one only for this dock would be a bigger, less consistent
 * change than a direct drag handle.
 */
Item {
    id: root

    property bool expanded: false
    property real expandedHeight: 220
    readonly property real minExpandedHeight: 140
    // Overridable, not fixed: a 420px dock at the 1366x768 floor would
    // leave the engineering object too little room to "stay meaningful,"
    // which RF_WORKBENCH_GRAMMAR.md's responsive rule requires (shrink the
    // object, never hide it) -- found by manually inspecting
    // acceptance/cad_workbench_r1/rocket_performance/performance_1366x768_dock_expanded_tall.png
    // during the rf-visual-qa pass, not assumed. The caller (ui/Main.qml)
    // binds this to a fraction of window height so the workspace above the
    // dock always keeps at least half the vertical space, regardless of
    // how far the dock has been dragged.
    property real maxExpandedHeight: 420
    readonly property real collapsedHeight: 32

    property int currentTab: 0
    // [{ label: string, available: bool }]
    property var tabs: []

    default property alias content: contentHolder.data

    function open(tabIndex) {
        currentTab = tabIndex
        expanded = true
    }

    // Re-clamp if the ceiling itself moves (a window resize while the dock
    // is open at a height the new, smaller maximum no longer allows) --
    // the DragHandler's own clamp only fires on a drag gesture.
    onMaxExpandedHeightChanged: {
        if (expandedHeight > maxExpandedHeight)
            expandedHeight = maxExpandedHeight
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

    // ---- drag-to-resize handle --------------------------------------------
    // A thin strip on the top edge, active only while expanded. Dragging
    // adjusts expandedHeight directly and clamps it, the same "the real
    // value is the source of truth" discipline CollapsiblePanel uses for
    // width, applied to height.
    Item {
        id: resizeHandle
        visible: root.expanded
        width: parent.width
        height: 6
        y: -3
        z: 10

        HoverHandler { id: handleHover; cursorShape: Qt.SizeVerCursor }

        DragHandler {
            target: null
            property real dragStartHeight: root.expandedHeight
            onActiveChanged: {
                if (active) dragStartHeight = root.expandedHeight
            }
            onTranslationChanged: {
                let next = dragStartHeight - translation.y
                root.expandedHeight = Math.max(root.minExpandedHeight,
                                               Math.min(root.maxExpandedHeight, next))
            }
        }

        Rectangle {
            anchors.centerIn: parent
            width: 32
            height: Metrics.hairline
            color: handleHover.hovered ? Theme.borderStrong : Theme.divider
            Behavior on color { ColorAnimation { duration: Motion.fast } }
        }
    }

    // ---- tab strip ----------------------------------------------------
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
                model: root.tabs

                delegate: Item {
                    id: tabItem
                    required property var modelData
                    required property int index

                    readonly property bool current: root.expanded && root.currentTab === index
                    readonly property bool tabAvailable: modelData.available !== false

                    width: tabLabel.implicitWidth + Metrics.spacing.m
                    height: root.collapsedHeight - 6
                    anchors.verticalCenter: parent.verticalCenter

                    Rectangle {
                        anchors.fill: parent
                        radius: Metrics.radius.m
                        color: tabItem.current ? Theme.surface
                             : tabHover.hovered && tabItem.tabAvailable ? Theme.surfaceHover
                             : "transparent"
                        Behavior on color { ColorAnimation { duration: Motion.fast } }
                    }

                    Text {
                        id: tabLabel
                        anchors.centerIn: parent
                        text: tabItem.modelData.label
                        color: !tabItem.tabAvailable ? Theme.textDisabled
                             : tabItem.current ? Theme.text : Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.bodySmall
                        font.weight: tabItem.current ? Typography.medium : Typography.regular
                        Behavior on color { ColorAnimation { duration: Motion.fast } }
                    }

                    HoverHandler {
                        id: tabHover
                        cursorShape: tabItem.tabAvailable ? Qt.PointingHandCursor : Qt.ArrowCursor
                    }

                    TapHandler {
                        enabled: tabItem.tabAvailable
                        onTapped: {
                            if (root.expanded && root.currentTab === tabItem.index)
                                root.expanded = false
                            else
                                root.open(tabItem.index)
                        }
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
            tooltip: root.expanded ? "Collapse dock" : "Expand dock"
            onClicked: root.expanded = !root.expanded

            Behavior on rotation {
                NumberAnimation { duration: Motion.base; easing.type: Motion.standard }
            }
        }
    }

    // ---- content ---------------------------------------------------------
    Item {
        id: contentHolder
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
    }
}
