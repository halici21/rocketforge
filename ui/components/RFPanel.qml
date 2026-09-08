import QtQuick
import QtQuick.Layouts
import "../theme"

/*
 * RFPanel - the only surface container in the application.
 *
 * Children are laid out in a ColumnLayout, so a panel can hold a stack of
 * fields or a single item that fills it (a plot, a drawing). Panels are used
 * to group content, never to decorate it: no shadow, no gradient, one hairline.
 */
Rectangle {
    id: root

    property string title: ""
    property Component trailing: null
    property real contentPadding: Metrics.panelPadding
    property real contentSpacing: Metrics.spacing.m

    default property alias content: body.data

    color: Theme.surface
    radius: Metrics.radius.xl
    border.width: Metrics.hairline
    border.color: Theme.border

    implicitWidth: outer.implicitWidth + contentPadding * 2
    implicitHeight: outer.implicitHeight + contentPadding * 2

    Behavior on color { ColorAnimation { duration: Motion.fast } }
    Behavior on border.color { ColorAnimation { duration: Motion.fast } }

    ColumnLayout {
        id: outer
        anchors.fill: parent
        anchors.margins: root.contentPadding
        spacing: header.visible ? Metrics.spacing.m : 0

        RowLayout {
            id: header
            visible: root.title !== "" || root.trailing !== null
            Layout.fillWidth: true
            spacing: Metrics.spacing.s

            RFSectionLabel {
                text: root.title
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter
            }

            Loader {
                sourceComponent: root.trailing
                Layout.alignment: Qt.AlignVCenter
            }
        }

        ColumnLayout {
            id: body
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: root.contentSpacing
        }
    }
}
