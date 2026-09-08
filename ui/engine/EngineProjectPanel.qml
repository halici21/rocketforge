import QtQuick
import QtQuick.Controls
import "../theme"
import "../components"
import "model"
import "visuals"

/*
 * The project hierarchy: the engine, the subsystems its components fall into,
 * and the studies that will run on it.
 *
 * The component list used to be flat, which is fine at seven parts and useless
 * at forty: a staged-combustion engine with two turbopumps, two preburners and
 * a cooling circuit is sixty rows of alphabet soup. So components are filed
 * under the subsystem their type belongs to, and each subsystem folds away.
 *
 * The grouping is registry metadata - the category a component type was
 * declared in - and not an inference about this particular engine. Nothing here
 * reads the graph to work out what a part is for, because deciding that needs
 * physics this build does not have.
 *
 * A subsystem with nothing in it is not drawn, so the tree starts as small as
 * the engine is and grows structure only as the engine earns it.
 *
 * Selection is shared with the canvas in both directions: this is a second view
 * of one graph, not a copy of it.
 */
Item {
    id: root

    property Item canvas: null

    // Groups are open by default and remember being shut, keyed by category id.
    property var collapsedGroups: ({})

    function groupOpen(id) {
        return collapsedGroups[id] !== true
    }

    function toggleGroup(id) {
        var next = {}
        for (var k in collapsedGroups)
            next[k] = collapsedGroups[k]
        next[id] = groupOpen(id)
        collapsedGroups = next
    }

    // The components of one subsystem, in the order they were added.
    function componentsIn(categoryId) {
        EngineModel.graphRevision
        var out = []
        for (var i = 0; i < EngineModel.nodes.count; ++i) {
            var n = EngineModel.nodes.get(i)
            if (ComponentRegistry.categoryOf(n.type) === categoryId)
                out.push(n.nodeId)
        }
        return out
    }

    // ---- inline pieces ---------------------------------------------------

    component GroupHeader: Item {
        id: header
        property string title: ""
        property string note: ""
        property bool expanded: true
        signal toggled()

        width: parent ? parent.width : 0
        height: Metrics.navGroupHeight + Metrics.spacing.s

        Rectangle {
            anchors.fill: parent
            anchors.leftMargin: Metrics.spacing.s
            anchors.rightMargin: Metrics.spacing.s
            anchors.topMargin: Metrics.spacing.xs
            radius: Metrics.radius.m
            color: headerHover.hovered ? Theme.surface : "transparent"
            Behavior on color { ColorAnimation { duration: Motion.fast } }
        }

        RFIcon {
            id: chevron
            x: Metrics.spacing.m
            anchors.verticalCenter: parent.verticalCenter
            anchors.verticalCenterOffset: 2
            name: "chevron-down"
            width: 12
            height: 12
            color: Theme.textMuted
            rotation: header.expanded ? 0 : -90
            Behavior on rotation {
                NumberAnimation { duration: Motion.base; easing.type: Motion.standard }
            }
        }

        RFSectionLabel {
            id: headerLabel
            anchors.left: chevron.right
            anchors.leftMargin: Metrics.spacing.s
            anchors.verticalCenter: parent.verticalCenter
            anchors.verticalCenterOffset: 2
            text: header.title
            font.pixelSize: Typography.navGroup
            font.letterSpacing: Typography.navGroupTracking
        }

        Text {
            anchors.left: headerLabel.right
            anchors.leftMargin: Metrics.spacing.s
            anchors.baseline: headerLabel.baseline
            text: header.note
            color: Theme.textDisabled
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }

        HoverHandler { id: headerHover; cursorShape: Qt.PointingHandCursor }
        TapHandler { onTapped: header.toggled() }
    }

    // A folding body, so every group in the tree opens the same way.
    component GroupBody: Item {
        id: bodyItem
        property bool expanded: true
        default property alias items: bodyColumn.data

        width: parent ? parent.width : 0
        height: expanded ? bodyColumn.implicitHeight : 0
        clip: true

        Behavior on height {
            NumberAnimation { duration: Motion.base; easing.type: Motion.standard }
        }

        Column {
            id: bodyColumn
            width: parent.width
            opacity: bodyItem.expanded ? 1 : 0
            Behavior on opacity { NumberAnimation { duration: Motion.base } }
        }
    }

    component PlannedRow: RFNavItem {
        available: false
        indent: Metrics.spacing.h1
        width: parent ? parent.width : 0
    }

    // One component, indented under its subsystem so the hierarchy reads
    // without a second column of guide lines.
    component ComponentRow: Item {
        id: componentRow
        property string nodeId: ""

        readonly property var node: {
            EngineModel.graphRevision
            return EngineModel.node(nodeId)
        }
        readonly property bool current: {
            EngineModel.selectedNodes
            return EngineModel.isNodeSelected(nodeId)
        }
        readonly property string status: {
            EngineModel.graphRevision
            return EngineModel.nodeStatus(nodeId)
        }

        width: parent ? parent.width : 0
        height: Metrics.navItemHeight

        Rectangle {
            anchors.fill: parent
            anchors.leftMargin: Metrics.spacing.s
            anchors.rightMargin: Metrics.spacing.s
            radius: Metrics.radius.m
            color: componentRow.current ? Theme.surfaceHover
                 : rowHover.hovered ? Theme.surface : "transparent"
            Behavior on color { ColorAnimation { duration: Motion.fast } }
        }

        Rectangle {
            x: Metrics.spacing.s + 1
            anchors.verticalCenter: parent.verticalCenter
            width: 2
            height: componentRow.current ? 14 : 0
            radius: 1
            color: Theme.accent
            Behavior on height {
                NumberAnimation { duration: Motion.base; easing.type: Motion.standard }
            }
        }

        ComponentGlyph {
            id: rowGlyph
            x: Metrics.spacing.xxl
            anchors.verticalCenter: parent.verticalCenter
            width: 15
            height: 15
            glyph: componentRow.node ? ComponentRegistry.glyphFor(componentRow.node.type) : ""
            color: componentRow.current ? Theme.text : Theme.textMuted
        }

        Text {
            anchors.left: rowGlyph.right
            anchors.leftMargin: Metrics.spacing.s
            anchors.right: rowStatus.left
            anchors.rightMargin: Metrics.spacing.s
            anchors.verticalCenter: parent.verticalCenter
            text: componentRow.node ? componentRow.node.name : ""
            elide: Text.ElideRight
            color: componentRow.node && !componentRow.node.enabled ? Theme.textDisabled
                 : componentRow.current ? Theme.text : Theme.textSecondary
            font.family: Typography.sans
            font.pixelSize: Typography.navItem
            font.weight: componentRow.current ? Typography.medium : Typography.regular
        }

        Rectangle {
            id: rowStatus
            anchors.right: parent.right
            anchors.rightMargin: Metrics.spacing.m + Metrics.spacing.xs
            anchors.verticalCenter: parent.verticalCenter
            width: componentRow.status === "disabled" ? 8 : 6
            height: componentRow.status === "disabled" ? 2 : 6
            rotation: componentRow.status === "problem" ? 45 : 0
            radius: componentRow.status === "configured"
                    || componentRow.status === "unconfigured" ? width / 2 : 0.5
            color: componentRow.status === "configured" ? Theme.success
                 : componentRow.status === "problem" ? Theme.warning
                 : componentRow.status === "disabled" ? Theme.textDisabled
                 : "transparent"
            border.width: componentRow.status === "unconfigured" ? 1.2 : 0
            border.color: Theme.textMuted
        }

        HoverHandler { id: rowHover; cursorShape: Qt.PointingHandCursor }

        TapHandler {
            onTapped: EngineModel.selectNode(componentRow.nodeId, false)
            onDoubleTapped: {
                if (root.canvas) {
                    root.canvas.focusNode(componentRow.nodeId)
                    root.canvas.openComponentWorkspace(componentRow.nodeId)
                }
            }
        }
    }

    // ---- content ---------------------------------------------------------

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

            // ---- engine header -------------------------------------------
            Item {
                width: parent.width
                height: 54

                Column {
                    x: Metrics.spacing.m + Metrics.spacing.xs
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 2

                    Text {
                        text: EngineModel.engineName
                        color: Theme.text
                        font.family: Typography.sans
                        font.pixelSize: Typography.body
                        font.weight: Typography.semibold
                        font.letterSpacing: 0.2
                    }
                    Text {
                        text: EngineModel.architecture + "  ·  " + EngineModel.propellants
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                }
            }

            Rectangle {
                x: Metrics.spacing.m
                width: parent.width - Metrics.spacing.m * 2
                height: Metrics.hairline
                color: Theme.divider
            }

            // ---- architecture: one group per subsystem -------------------

            Item {
                width: parent.width
                height: Metrics.navGroupHeight + Metrics.spacing.s

                RFSectionLabel {
                    x: Metrics.spacing.m
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.verticalCenterOffset: 2
                    text: "Architecture"
                    font.pixelSize: Typography.navGroup
                    font.letterSpacing: Typography.navGroupTracking
                }

                Text {
                    anchors.right: parent.right
                    anchors.rightMargin: Metrics.spacing.m + Metrics.spacing.xs
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.verticalCenterOffset: 2
                    text: EngineModel.nodes.count > 0
                          ? EngineModel.nodes.count + " components" : ""
                    color: Theme.textDisabled
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }

            Repeater {
                model: ComponentRegistry.categories

                delegate: Column {
                    id: subsystem
                    required property var modelData

                    readonly property var ids: root.componentsIn(modelData.id)

                    width: column.width
                    visible: ids.length > 0

                    GroupHeader {
                        title: subsystem.modelData.subsystem
                        note: subsystem.ids.length + ""
                        expanded: root.groupOpen(subsystem.modelData.id)
                        onToggled: root.toggleGroup(subsystem.modelData.id)
                    }

                    GroupBody {
                        expanded: root.groupOpen(subsystem.modelData.id)

                        Repeater {
                            model: subsystem.ids
                            delegate: ComponentRow {
                                required property var modelData
                                nodeId: modelData
                            }
                        }
                    }
                }
            }

            // Nothing placed yet.
            Item {
                width: column.width
                height: EngineModel.nodes.count === 0 ? 46 : 0
                visible: EngineModel.nodes.count === 0

                Text {
                    x: Metrics.spacing.h1
                    anchors.verticalCenter: parent.verticalCenter
                    width: parent.width - Metrics.spacing.h1 - Metrics.spacing.m
                    text: "No components yet."
                    wrapMode: Text.WordWrap
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                }
            }

            Item { width: 1; height: Metrics.spacing.s }

            // ---- studies -------------------------------------------------
            GroupHeader {
                title: "Studies"
                note: "planned"
                expanded: root.groupOpen("studies")
                onToggled: root.toggleGroup("studies")
            }

            GroupBody {
                expanded: root.groupOpen("studies")

                Repeater {
                    model: MockEngineData.studies
                    delegate: PlannedRow {
                        required property var modelData
                        label: modelData
                    }
                }
            }

            Item { width: 1; height: Metrics.spacing.l }
        }
    }
}
