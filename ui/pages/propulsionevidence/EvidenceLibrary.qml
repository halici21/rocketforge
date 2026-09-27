import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * The library drawer's contents: filters, then the records they leave.
 *
 * Every option and every row comes from the controller, which derives them from
 * the shipped records -- a status nobody holds is not offered, and a section
 * with no records is not drawn. Picking a filter or a record is view state.
 */
ColumnLayout {
    id: root

    spacing: Metrics.spacing.m

    readonly property var options: PropulsionEvidence.filterOptions

    function keysOf(list) { return list.map(function (o) { return o.key }) }
    function labelsOf(list, any) { return [any].concat(list.map(function (o) { return o.label })) }

    RFComboBox {
        objectName: "evidenceStatusFilter"
        Layout.fillWidth: true
        label: "Status"
        model: root.labelsOf(root.options.status, "Any status")
        currentIndex: root.keysOf(root.options.status).indexOf(PropulsionEvidence.filterStatus) + 1
        onActivated: function (index) {
            PropulsionEvidence.setFilterStatus(index > 0 ? root.options.status[index - 1].key : "")
        }
    }

    RFComboBox {
        objectName: "evidenceDimensionFilter"
        Layout.fillWidth: true
        label: "Status in dimension"
        model: root.labelsOf(root.options.dimension, "Any dimension")
        currentIndex: root.keysOf(root.options.dimension).indexOf(PropulsionEvidence.filterDimension) + 1
        onActivated: function (index) {
            PropulsionEvidence.setFilterDimension(index > 0 ? root.options.dimension[index - 1].key : "")
        }
    }

    RFComboBox {
        objectName: "evidenceShippingFilter"
        Layout.fillWidth: true
        label: "Source shipping policy"
        model: root.labelsOf(root.options.shipping, "Any policy")
        currentIndex: root.keysOf(root.options.shipping).indexOf(PropulsionEvidence.filterShipping) + 1
        onActivated: function (index) {
            PropulsionEvidence.setFilterShipping(index > 0 ? root.options.shipping[index - 1].key : "")
        }
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: Metrics.spacing.s

        Text {
            Layout.fillWidth: true
            text: PropulsionEvidence.visibleCount + " of " + PropulsionEvidence.recordCount
                  + (PropulsionEvidence.recordCount === 1 ? " record" : " records")
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
        RFToolButton {
            objectName: "evidenceLibraryClear"
            visible: PropulsionEvidence.hasActiveFilter
            text: "Clear filters"
            onClicked: PropulsionEvidence.clearFilters()
        }
    }

    RFDivider { Layout.fillWidth: true }

    ListView {
        id: list
        objectName: "evidenceLibraryList"
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        spacing: 2
        boundsBehavior: Flickable.StopAtBounds
        model: PropulsionEvidence.library
        ScrollBar.vertical: RFScrollBar {}

        delegate: Column {
            id: entry
            required property string recordId
            required property string title
            required property string section
            required property bool sectionStart
            required property string capabilities

            readonly property bool selected: entry.recordId === PropulsionEvidence.selectedRecordId

            width: ListView.view.width
            spacing: 2

            RFSectionLabel {
                visible: entry.sectionStart
                text: entry.section
                topPadding: Metrics.spacing.xs
                bottomPadding: Metrics.spacing.xs
            }

            Rectangle {
                width: parent.width
                height: rowColumn.implicitHeight + Metrics.spacing.s * 2
                radius: Metrics.radius.s
                color: entry.selected ? Theme.surfaceHover
                       : rowArea.containsMouse ? Theme.surfaceSubtle : "transparent"
                activeFocusOnTab: true
                Accessible.role: Accessible.ListItem
                Accessible.name: entry.title
                Keys.onReturnPressed: PropulsionEvidence.selectRecord(entry.recordId)
                Keys.onSpacePressed: PropulsionEvidence.selectRecord(entry.recordId)

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
                        text: entry.recordId
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
                    onClicked: PropulsionEvidence.selectRecord(entry.recordId)
                }
            }
        }
    }
}
