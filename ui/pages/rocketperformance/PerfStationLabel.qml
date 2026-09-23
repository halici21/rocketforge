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
        text: Notation.rich(root.title)
        textFormat: Notation.textFormat(root.title)
        color: Theme.textSecondary
        font.family: Typography.sans
        font.pixelSize: Typography.sectionLabel
        font.letterSpacing: Typography.sectionTracking
        font.weight: Typography.medium
    }

    Text {
        visible: root.detail !== ""
        readonly property string plainText: root.detail
        text: Notation.rich(plainText)
        textFormat: Notation.textFormat(plainText)
        color: Theme.textSecondary
        font.family: Typography.mono
        font.pixelSize: Typography.readoutSmall
    }
}
