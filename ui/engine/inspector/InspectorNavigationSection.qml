import QtQuick
import "../../theme"
import "../../components"

/*
 * A way out of the panel and into somewhere the work actually happens.
 *
 * Kept as its own component because navigation is the piece of the inspector
 * that has to disappear in the wrong context: an action that opens the very
 * workspace already filling the screen is noise, and the surest way to avoid
 * shipping one is to make its presence a decision the caller has to take.
 */
InspectorSection {
    id: root

    property string label: ""
    property string description: ""
    property string icon: "chevron-right"

    signal activated()

    RFButton {
        width: parent.width
        text: root.label
        icon: root.icon
        compact: true
        onClicked: root.activated()
    }

    Text {
        width: parent.width
        visible: root.description !== ""
        text: root.description
        wrapMode: Text.WordWrap
        lineHeight: Typography.proseLineHeight
        lineHeightMode: Text.ProportionalHeight
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.meta
    }
}
