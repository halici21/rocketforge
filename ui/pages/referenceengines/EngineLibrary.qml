import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * The library drawer's contents: search, filters, then the configurations they
 * leave, grouped by family.
 *
 * Every option and every row comes from the ReferenceEngines controller, which
 * derives them from the shipped corpus -- a status or cycle nobody holds is not
 * offered. Typing, picking a filter or picking a configuration is view state.
 */
ColumnLayout {
    id: root

    spacing: Metrics.spacing.m

    readonly property var options: ReferenceEngines.filterOptions

    function keysOf(list) { return list.map(function (o) { return o.key }) }
    function labelsOf(list, any) { return [any].concat(list.map(function (o) { return o.label })) }

    RFTextField {
        id: search
        objectName: "engineSearch"
        Layout.fillWidth: true
        label: "Find an engine"
        placeholder: "Name, designation, family or alias"
        onTextChanged: ReferenceEngines.setSearch(search.text)
        Connections {
            target: ReferenceEngines
            // Clear filters also clears the field, so the two never disagree.
            function onFiltersChanged() {
                if (ReferenceEngines.filterSearch === "" && search.text !== "")
                    search.text = ""
            }
        }
    }

    RFComboBox {
        objectName: "engineCapabilityFilter"
        Layout.fillWidth: true
        label: "Capability"
        model: root.labelsOf(root.options.capability, "Any capability")
        currentIndex: root.keysOf(root.options.capability).indexOf(ReferenceEngines.filterCapability) + 1
        onActivated: function (index) {
            ReferenceEngines.setFilterCapability(index > 0 ? root.options.capability[index - 1].key : "")
        }
    }

    RFComboBox {
        objectName: "engineStatusFilter"
        Layout.fillWidth: true
        // A status means something only for one capability: it waits for one.
        enabled: ReferenceEngines.filterCapability !== ""
        label: "Status of that capability"
        model: root.labelsOf(root.options.status, ReferenceEngines.filterCapability !== ""
                                                  ? "Any status" : "Choose a capability first")
        currentIndex: root.keysOf(root.options.status).indexOf(ReferenceEngines.filterStatus) + 1
        onActivated: function (index) {
            ReferenceEngines.setFilterStatus(index > 0 ? root.options.status[index - 1].key : "")
        }
    }

    RFComboBox {
        objectName: "engineCycleFilter"
        Layout.fillWidth: true
        label: "Recorded cycle"
        model: root.labelsOf(root.options.cycle, "Any cycle")
        currentIndex: root.keysOf(root.options.cycle).indexOf(ReferenceEngines.filterCycle) + 1
        onActivated: function (index) {
            ReferenceEngines.setFilterCycle(index > 0 ? root.options.cycle[index - 1].key : "")
        }
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: Metrics.spacing.s

        Text {
            objectName: "engineLibraryCount"
            Layout.fillWidth: true
            text: ReferenceEngines.visibleCount + " of " + ReferenceEngines.configurationCount
                  + (ReferenceEngines.configurationCount === 1 ? " configuration" : " configurations")
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
        RFToolButton {
            objectName: "engineLibraryClear"
            visible: ReferenceEngines.hasActiveFilter
            text: "Clear filters"
            onClicked: ReferenceEngines.clearFilters()
        }
    }

    RFDivider { Layout.fillWidth: true }

    ListView {
        id: list
        objectName: "engineLibraryList"
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        spacing: 2
        boundsBehavior: Flickable.StopAtBounds
        model: ReferenceEngines.library
        ScrollBar.vertical: RFScrollBar {}

        delegate: Column {
            id: entry
            required property string configurationId
            required property string title
            required property string subtitle
            required property string section
            required property bool sectionStart
            required property string capabilities

            readonly property bool selected: entry.configurationId === ReferenceEngines.selectedConfigurationId

            width: ListView.view.width
            spacing: 2

            RFSectionLabel {
                visible: entry.sectionStart
                text: entry.section
                topPadding: Metrics.spacing.xs
                bottomPadding: Metrics.spacing.xs
            }

            Rectangle {
                objectName: "engineRow_" + entry.configurationId
                width: parent.width
                height: rowColumn.implicitHeight + Metrics.spacing.s * 2
                radius: Metrics.radius.s
                color: entry.selected ? Theme.surfaceHover
                       : rowArea.containsMouse ? Theme.surfaceSubtle : "transparent"
                activeFocusOnTab: true
                Accessible.role: Accessible.ListItem
                Accessible.name: entry.title
                Keys.onReturnPressed: ReferenceEngines.selectConfiguration(entry.configurationId)
                Keys.onSpacePressed: ReferenceEngines.selectConfiguration(entry.configurationId)

                RFProximityEdge { active: parent.activeFocus }

                // Selection is marked twice: an accent edge and a weight change.
                Rectangle {
                    visible: entry.selected
                    width: 2
                    height: parent.height - Metrics.spacing.s
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    radius: 1
                    color: Theme.accent
                }

                Column {
                    id: rowColumn
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.leftMargin: Metrics.spacing.m
                    anchors.rightMargin: Metrics.spacing.s
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 3

                    Text {
                        width: parent.width
                        text: entry.title
                        wrapMode: Text.WordWrap
                        maximumLineCount: 3
                        elide: Text.ElideRight
                        color: Theme.text
                        font.family: Typography.sans
                        font.pixelSize: Typography.bodySmall
                        font.weight: entry.selected ? Typography.semibold : Typography.regular
                    }
                    Text {
                        width: parent.width
                        text: entry.configurationId
                        elide: Text.ElideRight
                        color: Theme.textSecondary
                        font.family: Typography.mono
                        font.pixelSize: Typography.meta
                    }
                    Text {
                        width: parent.width
                        text: entry.capabilities
                        wrapMode: Text.WordWrap
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                }

                MouseArea {
                    id: rowArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: ReferenceEngines.selectConfiguration(entry.configurationId)
                }
            }
        }
    }
}
