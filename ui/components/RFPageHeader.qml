import QtQuick
import "../theme"

/*
 * Every workspace page opens the same way: name, one line of orientation, and
 * page-level actions pushed to the right.
 */
Item {
    id: root

    property string title: ""
    property string subtitle: ""
    property Component trailing: null

    implicitHeight: Math.max(titleText.implicitHeight + subtitleText.implicitHeight + 2,
                             trailingLoader.implicitHeight)

    Text {
        id: titleText
        text: root.title
        color: Theme.text
        font.family: Typography.sans
        font.pixelSize: Typography.pageTitle
        font.weight: Typography.semibold
        font.letterSpacing: Typography.titleTracking
    }

    Text {
        id: subtitleText
        anchors.top: titleText.bottom
        anchors.topMargin: 2
        text: root.subtitle
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.pageSubtitle
    }

    Loader {
        id: trailingLoader
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        sourceComponent: root.trailing
    }
}
