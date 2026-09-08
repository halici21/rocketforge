import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"
import "../components"
import "../data"

/*
 * The module navigator.
 *
 * Structure is carried by typography and indentation rather than by icons:
 * a domain heading, quiet group labels, and rows whose only decoration is the
 * accent marker on the current one. The second domain of the product is
 * present but folded away, so the shape of the roadmap is visible without
 * crowding the modules that work.
 */
Item {
    id: root

    property int currentIndex: 0
    property bool engineSectionExpanded: false
    property bool engineModeActive: false

    signal selected(int index)
    signal engineModeRequested()

    clip: true
    activeFocusOnTab: true

    function step(delta) {
        var next = Math.max(0, Math.min(Navigation.items.length - 1, currentIndex + delta))
        if (next !== currentIndex)
            root.selected(next)
    }

    Keys.onUpPressed: step(-1)
    Keys.onDownPressed: step(1)

    // Shell chrome sits one step off the workspace so the two read as
    // different layers without a border between them.
    Rectangle {
        anchors.fill: parent
        color: Theme.surfaceSubtle
        Behavior on color { ColorAnimation { duration: Motion.fast } }
    }

    Flickable {
        anchors.fill: parent
        contentWidth: width
        contentHeight: column.implicitHeight
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: RFScrollBar {}

        ColumnLayout {
            id: column
            width: root.width
            spacing: 0

            // ---- compressible flow domain --------------------------------
            Item { Layout.preferredHeight: Metrics.spacing.m }

            RFSectionLabel {
                text: Navigation.flowDomain
                strong: true
                Layout.leftMargin: Metrics.spacing.m + Metrics.spacing.xs
                Layout.rightMargin: Metrics.spacing.m
                Layout.fillWidth: true
            }

            Item { Layout.preferredHeight: Metrics.spacing.s }

            Repeater {
                model: Navigation.flowRows

                delegate: Item {
                    id: row
                    required property var modelData

                    readonly property bool isGroup: modelData.kind === "group"
                    readonly property int itemIndex: modelData.kind === "item" ? modelData.index : -1

                    Layout.fillWidth: true
                    Layout.preferredHeight: isGroup ? Metrics.navGroupHeight + Metrics.spacing.s
                                                    : Metrics.navItemHeight

                    RFSectionLabel {
                        visible: row.isGroup
                        text: row.isGroup ? row.modelData.label : ""
                        font.pixelSize: Typography.navGroup
                        font.letterSpacing: Typography.navGroupTracking
                        x: Metrics.spacing.m + Metrics.spacing.xs
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: Metrics.spacing.xs + 1
                    }

                    RFNavItem {
                        visible: !row.isGroup
                        anchors.fill: parent
                        label: row.itemIndex >= 0 ? Navigation.items[row.itemIndex].label : ""
                        current: row.itemIndex === root.currentIndex
                        onActivated: root.selected(row.itemIndex)
                    }
                }
            }

            // ---- thermochemistry domain ----------------------------------
            // A second analysis domain rather than another compressible
            // module: its numbers come from a chemistry provider, so putting
            // it under the COMPRESSIBLE FLOW heading would misfile it.
            Item { Layout.preferredHeight: Metrics.spacing.l }

            Rectangle {
                Layout.fillWidth: true
                Layout.leftMargin: Metrics.spacing.m
                Layout.rightMargin: Metrics.spacing.m
                Layout.preferredHeight: Metrics.hairline
                color: Theme.divider
            }

            Item { Layout.preferredHeight: Metrics.spacing.m }

            RFSectionLabel {
                text: Navigation.chemistryDomain
                strong: true
                Layout.leftMargin: Metrics.spacing.m + Metrics.spacing.xs
                Layout.rightMargin: Metrics.spacing.m
                Layout.fillWidth: true
            }

            Item { Layout.preferredHeight: Metrics.spacing.s }

            Repeater {
                model: Navigation.chemistryRows

                delegate: RFNavItem {
                    required property var modelData

                    Layout.fillWidth: true
                    Layout.preferredHeight: Metrics.navItemHeight
                    label: Navigation.items[modelData.index].label
                    current: modelData.index === root.currentIndex
                    onActivated: root.selected(modelData.index)
                }
            }

            // ---- rocket performance domain -------------------------------
            Item { Layout.preferredHeight: Metrics.spacing.m }

            RFSectionLabel {
                text: Navigation.performanceDomain
                strong: true
                Layout.leftMargin: Metrics.spacing.m + Metrics.spacing.xs
                Layout.rightMargin: Metrics.spacing.m
                Layout.fillWidth: true
            }

            Item { Layout.preferredHeight: Metrics.spacing.s }

            Repeater {
                model: Navigation.performanceRows

                delegate: RFNavItem {
                    required property var modelData

                    Layout.fillWidth: true
                    Layout.preferredHeight: Metrics.navItemHeight
                    label: Navigation.items[modelData.index].label
                    current: modelData.index === root.currentIndex
                    onActivated: root.selected(modelData.index)
                }
            }

            // ---- trade study domain --------------------------------------
            Item { Layout.preferredHeight: Metrics.spacing.m }

            RFSectionLabel {
                text: Navigation.studyDomain
                strong: true
                Layout.leftMargin: Metrics.spacing.m + Metrics.spacing.xs
                Layout.rightMargin: Metrics.spacing.m
                Layout.fillWidth: true
            }

            Item { Layout.preferredHeight: Metrics.spacing.s }

            Repeater {
                model: Navigation.studyRows

                delegate: RFNavItem {
                    required property var modelData

                    Layout.fillWidth: true
                    Layout.preferredHeight: Metrics.navItemHeight
                    label: Navigation.items[modelData.index].label
                    current: modelData.index === root.currentIndex
                    onActivated: root.selected(modelData.index)
                }
            }

            // ---- fluid properties domain ---------------------------------
            Item { Layout.preferredHeight: Metrics.spacing.m }

            RFSectionLabel {
                text: Navigation.fluidDomain
                strong: true
                Layout.leftMargin: Metrics.spacing.m + Metrics.spacing.xs
                Layout.rightMargin: Metrics.spacing.m
                Layout.fillWidth: true
            }

            Item { Layout.preferredHeight: Metrics.spacing.s }

            Repeater {
                model: Navigation.fluidRows

                delegate: RFNavItem {
                    required property var modelData

                    Layout.fillWidth: true
                    Layout.preferredHeight: Metrics.navItemHeight
                    label: Navigation.items[modelData.index].label
                    current: modelData.index === root.currentIndex
                    onActivated: root.selected(modelData.index)
                }
            }

            // ---- rocket engine domain ------------------------------------
            Item { Layout.preferredHeight: Metrics.spacing.l }

            Rectangle {
                Layout.fillWidth: true
                Layout.leftMargin: Metrics.spacing.m
                Layout.rightMargin: Metrics.spacing.m
                Layout.preferredHeight: Metrics.hairline
                color: Theme.divider
            }

            Item {
                id: engineHeader
                Layout.fillWidth: true
                Layout.preferredHeight: Metrics.navGroupHeight + Metrics.spacing.s

                RFSectionLabel {
                    id: engineLabel
                    text: Navigation.engineDomain
                    strong: true
                    x: Metrics.spacing.m + Metrics.spacing.xs
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.verticalCenterOffset: 2
                }
            }

            // The workspace for the second domain of the product.
            RFNavItem {
                Layout.fillWidth: true
                label: "Engine Design"
                current: root.engineModeActive
                onActivated: root.engineModeRequested()
            }

            // The component design modules that will live inside it.
            Item {
                id: plannedHeader
                Layout.fillWidth: true
                Layout.preferredHeight: Metrics.navGroupHeight + Metrics.spacing.xs

                Rectangle {
                    anchors.fill: parent
                    anchors.leftMargin: Metrics.spacing.s
                    anchors.rightMargin: Metrics.spacing.s
                    radius: Metrics.radius.m
                    color: engineHover.hovered ? Theme.surface : "transparent"
                    Behavior on color { ColorAnimation { duration: Motion.fast } }
                }

                RFSectionLabel {
                    id: plannedLabel
                    text: "Modules"
                    x: Metrics.spacing.m + Metrics.spacing.l
                    anchors.verticalCenter: parent.verticalCenter
                    font.pixelSize: Typography.navGroup
                    font.letterSpacing: Typography.navGroupTracking
                }

                Text {
                    anchors.left: plannedLabel.right
                    anchors.leftMargin: Metrics.spacing.s
                    anchors.baseline: plannedLabel.baseline
                    text: Navigation.engineItems.length + " planned"
                    color: Theme.textDisabled
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                RFIcon {
                    anchors.right: parent.right
                    anchors.rightMargin: Metrics.spacing.m + Metrics.spacing.xs
                    anchors.verticalCenter: parent.verticalCenter
                    name: "chevron-down"
                    width: 13
                    height: 13
                    color: Theme.textMuted
                    rotation: root.engineSectionExpanded ? 0 : -90

                    Behavior on rotation {
                        NumberAnimation { duration: Motion.base; easing.type: Motion.standard }
                    }
                }

                HoverHandler { id: engineHover; cursorShape: Qt.PointingHandCursor }
                TapHandler { onTapped: root.engineSectionExpanded = !root.engineSectionExpanded }
            }

            // Folded away by default; the rows exist so the roadmap is legible.
            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: root.engineSectionExpanded
                                        ? engineColumn.implicitHeight : 0
                clip: true

                Behavior on Layout.preferredHeight {
                    NumberAnimation { duration: Motion.base; easing.type: Motion.standard }
                }

                Column {
                    id: engineColumn
                    width: parent.width
                    opacity: root.engineSectionExpanded ? 1 : 0

                    Behavior on opacity { NumberAnimation { duration: Motion.base } }

                    Repeater {
                        model: Navigation.engineItems

                        delegate: RFNavItem {
                            required property var modelData
                            width: engineColumn.width
                            indent: Metrics.spacing.h1
                            label: modelData
                            available: false
                            badge: "soon"
                        }
                    }
                }
            }

            Item { Layout.preferredHeight: Metrics.spacing.l }
        }
    }
}
