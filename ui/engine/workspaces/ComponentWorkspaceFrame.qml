import QtQuick
import QtQuick.Layouts
import "../../theme"
import "../../components"
import "../model"
import "../visuals"

/*
 * The shared frame for every detailed component workspace: identity, the
 * component's own section tabs, and one content area.
 *
 * Four bands of navigation stack up before any engineering is on screen - the
 * application bar, the document tabs, this identity line and these section tabs
 * - and each one is individually defensible. Together they were eating the top
 * of the page, so identity and sections share a row whenever the workspace is
 * wide enough to carry both, and drop to two rows only when it is not. Nothing
 * is removed; the hierarchy is folded rather than cut.
 *
 * The title is set at group weight rather than page weight for the same reason:
 * the document tab above already says which component this is, so restating it
 * at 21 px is a second answer to a question nobody asked twice.
 *
 * Sections beyond the overview are declared but not built. They stay visible
 * and say so on hover, which is how the product shape is communicated without
 * pretending the sections exist.
 */
Item {
    id: root

    property string nodeId: ""
    property var tabs: ["Overview"]
    property string note: ""
    property int currentTab: 0

    default property alias content: body.data

    readonly property var node: {
        EngineModel.graphRevision
        return EngineModel.node(nodeId)
    }
    readonly property var definition: node ? ComponentRegistry.definition(node.type) : null
    readonly property string status: {
        EngineModel.graphRevision
        return EngineModel.nodeStatus(nodeId)
    }

    readonly property real tabsWidth: Math.min(root.tabs.length * 104, 580)
    // Identity needs roughly a third of the line before the tabs may share it.
    readonly property bool inlineTabs: width > tabsWidth + 340

    Component {
        id: sectionTabs

        RFSegmentedControl {
            height: Metrics.controlHeightSmall + 3
            model: root.tabs
            currentIndex: root.currentTab
            disabledIndices: {
                var list = []
                for (var i = 1; i < root.tabs.length; ++i)
                    list.push(i)
                return list
            }
            disabledNote: "Section arrives with the component module"
            onSelected: function (index) { root.currentTab = index }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.spacing.l
        anchors.topMargin: Metrics.spacing.m
        spacing: Metrics.spacing.m

        // ---- identity, and the sections when they fit beside it ----------

        RowLayout {
            Layout.fillWidth: true
            spacing: Metrics.spacing.l

            ComponentGlyph {
                Layout.alignment: Qt.AlignVCenter
                width: 22
                height: 22
                glyph: root.definition ? root.definition.glyph : ""
                color: Theme.accent
            }

            Text {
                Layout.alignment: Qt.AlignVCenter
                text: root.node ? root.node.name : "Component"
                elide: Text.ElideRight
                color: Theme.text
                font.family: Typography.sans
                font.pixelSize: Typography.groupLabel + 4
                font.weight: Typography.semibold
                font.letterSpacing: Typography.titleTracking
            }

            RFStatusChip {
                Layout.alignment: Qt.AlignVCenter
                text: root.definition ? root.definition.displayName : "Component"
                showDot: false
            }

            Item { Layout.fillWidth: true }

            Loader {
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredWidth: root.tabsWidth
                Layout.preferredHeight: Metrics.controlHeightSmall + 3
                active: root.inlineTabs
                visible: active
                sourceComponent: sectionTabs
            }

            RFStatusChip {
                Layout.alignment: Qt.AlignVCenter
                text: root.status === "configured" ? "Connected"
                    : root.status === "problem" ? "Incomplete"
                    : root.status === "disabled" ? "Disabled" : "Partial"
                tone: root.status === "configured" ? "success"
                    : root.status === "problem" ? "warning" : "neutral"
            }

            RFButton {
                Layout.alignment: Qt.AlignVCenter
                visible: root.width > 720
                text: "Export"
                variant: "quiet"
                icon: "export"
                compact: true
                enabled: false
            }
        }

        // ---- sections, when the identity line could not carry them -------

        Loader {
            Layout.preferredWidth: root.tabsWidth
            Layout.preferredHeight: active ? Metrics.controlHeightSmall + 3 : 0
            active: !root.inlineTabs
            visible: active
            sourceComponent: sectionTabs
        }

        Item {
            id: body
            Layout.fillWidth: true
            Layout.fillHeight: true
        }

        Text {
            Layout.fillWidth: true
            visible: root.note !== ""
            text: root.note
            wrapMode: Text.WordWrap
            lineHeight: Typography.proseLineHeight
            lineHeightMode: Text.ProportionalHeight
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
    }
}
