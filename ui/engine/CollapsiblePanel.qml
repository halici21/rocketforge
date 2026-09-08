import QtQuick
import QtQuick.Controls
import "../theme"

/*
 * A SplitView child that can fold away and come back.
 *
 * The awkward part is that SplitView owns the width it hands out, and writes
 * SplitView.preferredWidth itself the moment a handle is dragged. A declarative
 * binding to that property therefore survives exactly until the user first
 * resizes the panel, and then never works again. So the transition assigns the
 * width instead of binding it, and treats the item's real width as the source
 * of truth whenever a fold starts - which is what makes collapsing still behave
 * after the panel has been dragged to a new size.
 *
 * While folding, the width constraints are lifted; the panel would otherwise be
 * clamped at its own minimum and stop halfway. They are restored when the
 * animation lands, so a restored panel cannot be dragged below its floor.
 */
Item {
    id: root

    property bool collapsed: false
    property real expandedWidth: 264
    property real minimumWidth: 210
    property real maximumWidth: 380

    default property alias content: holder.data

    // The width to return to. Follows the handle while the panel is open, so a
    // panel that was widened reopens at the width the user chose.
    property real restoredWidth: expandedWidth

    // Driven by the animation, assigned onward to the attached property.
    property real panelWidth: expandedWidth

    readonly property bool transitioning: slide.running

    SplitView.preferredWidth: expandedWidth
    SplitView.minimumWidth: (collapsed || transitioning) ? 0 : root.minimumWidth
    SplitView.maximumWidth: (collapsed || transitioning) ? Math.max(1, panelWidth)
                                                         : root.maximumWidth
    SplitView.fillWidth: false

    // Kept in the layout for the length of the fold, then dropped entirely so
    // that no handle is left behind next to a panel that is not there.
    visible: !collapsed || transitioning
    clip: true

    onPanelWidthChanged: SplitView.preferredWidth = panelWidth

    onCollapsedChanged: {
        if (collapsed && width > 1)
            restoredWidth = Math.max(root.minimumWidth, width)
        slide.from = collapsed ? width : Math.min(panelWidth, 1)
        slide.to = collapsed ? 0 : restoredWidth
        slide.restart()
    }

    NumberAnimation {
        id: slide
        target: root
        property: "panelWidth"
        duration: Motion.base
        easing.type: Motion.emphasized
    }

    Item {
        id: holder
        anchors.fill: parent
    }
}
