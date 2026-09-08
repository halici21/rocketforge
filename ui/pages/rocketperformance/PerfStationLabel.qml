import QtQuick
import "../../theme"

/*
 * A station annotation on the propulsion canvas: CHAMBER, THROAT, EXIT.
 *
 * A micro label with one line of solved detail beneath it. Deliberately tiny
 * and quiet -- annotations describe the drawing, they do not compete with the
 * readout rail.
 */
Column {
    id: root

    property string title: ""
    property string detail: ""

    spacing: 2

    Text {
        text: root.title
        color: Theme.textSecondary
        font.family: Typography.sans
        font.pixelSize: Typography.sectionLabel
        font.letterSpacing: Typography.sectionTracking
        font.weight: Typography.medium
    }

    Text {
        visible: root.detail !== ""
        text: root.detail
        color: Theme.textSecondary
        font.family: Typography.mono
        font.pixelSize: Typography.readoutSmall
    }
}
