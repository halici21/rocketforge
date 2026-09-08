import QtQuick
import "../../theme"
import "../../components"

/*
 * One labelled block of the inspector. Sections are separated by space and a
 * single label, never by nested cards.
 */
Column {
    id: root

    property string title: ""
    default property alias content: body.data

    width: parent ? parent.width : 0
    spacing: Metrics.spacing.s

    RFSectionLabel {
        text: root.title
        visible: root.title !== ""
        width: parent.width
    }

    Column {
        id: body
        width: parent.width
        spacing: Metrics.spacing.xs
    }
}
