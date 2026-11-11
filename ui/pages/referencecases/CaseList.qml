import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * The four points, grouped by document. Each row names the point, its inputs
 * and its run state in words. It never shows a difference: the list is a way
 * to choose a point, not a ranking of them. Choosing one is view state and
 * computes nothing.
 */
ListView {
    id: list
    objectName: "referenceCasesList"

    clip: true
    spacing: 2
    boundsBehavior: Flickable.StopAtBounds
    model: ReferenceCases.browser
    ScrollBar.vertical: RFScrollBar {}

    delegate: Column {
        id: entry
        required property int index
        required property string pointKey
        required property string pointName
        required property string section
        required property bool sectionStart
        required property string inputsLine
        required property string pointState
        required property string pointStateWord

        readonly property bool selected: entry.index === ReferenceCases.selectedIndex

        width: ListView.view.width
        spacing: 2

        RFSectionLabel {
            width: parent.width
            visible: entry.sectionStart
            text: entry.section
            wrapMode: Text.WordWrap
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
            Accessible.name: entry.pointName + ", " + entry.pointStateWord
            Keys.onReturnPressed: ReferenceCases.select(entry.index)
            Keys.onSpacePressed: ReferenceCases.select(entry.index)

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
                    text: entry.pointName
                    wrapMode: Text.WordWrap
                    color: Theme.text
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                    font.weight: entry.selected ? Typography.semibold : Typography.regular
                }
                Text {
                    width: parent.width
                    text: entry.inputsLine
                    wrapMode: Text.WordWrap
                    color: Theme.textSecondary
                    font.family: Typography.mono
                    font.pixelSize: Typography.meta
                }
                Text {
                    width: parent.width
                    text: entry.pointStateWord
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
                onClicked: ReferenceCases.select(entry.index)
            }
        }
    }
}
