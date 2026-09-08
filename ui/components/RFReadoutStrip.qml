import QtQuick
import QtQuick.Layouts
import "../theme"

/*
 * The instrument readout: one horizontal band of quantities, evenly divided by
 * hairlines. This is the deliberate alternative to a wall of dashboard tiles -
 * the numbers belong to one state, so they share one surface.
 */
Rectangle {
    id: root

    property string title: ""
    property var model: []
    property string scale: "medium"
    property int highlightIndex: -1

    implicitHeight: content.implicitHeight + Metrics.spacing.m * 2
    color: Theme.surfaceSubtle
    radius: Metrics.radius.xl
    border.width: Metrics.hairline
    border.color: Theme.border

    Behavior on color { ColorAnimation { duration: Motion.fast } }

    RowLayout {
        id: content
        anchors.fill: parent
        anchors.margins: Metrics.spacing.m
        anchors.leftMargin: Metrics.spacing.l
        anchors.rightMargin: Metrics.spacing.l
        spacing: 0

        RFSectionLabel {
            text: root.title
            visible: root.title !== ""
            Layout.alignment: Qt.AlignVCenter
            Layout.rightMargin: Metrics.spacing.xl
            Layout.preferredWidth: implicitWidth
        }

        Repeater {
            model: root.model

            delegate: RowLayout {
                required property var modelData
                required property int index

                Layout.fillWidth: true
                spacing: 0

                Rectangle {
                    visible: index > 0
                    Layout.preferredWidth: Metrics.hairline
                    Layout.fillHeight: true
                    Layout.rightMargin: Metrics.spacing.l
                    Layout.topMargin: 2
                    Layout.bottomMargin: 2
                    color: Theme.divider
                }

                RFResultValue {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignVCenter
                    label: modelData.label
                    value: modelData.value
                    unit: modelData.unit !== undefined ? modelData.unit : ""
                    scale: root.scale
                    highlighted: index === root.highlightIndex
                }
            }
        }
    }
}
