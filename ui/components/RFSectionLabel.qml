import QtQuick
import "../theme"

/*
 * The one label style that opens every group of content: small, tracked,
 * uppercase, quiet. Write the text in sentence case; the control uppercases it.
 */
Text {
    property bool strong: false

    color: strong ? Theme.textSecondary : Theme.textMuted
    font.family: Typography.sans
    font.pixelSize: Typography.sectionLabel
    font.weight: Typography.semibold
    font.letterSpacing: Typography.sectionTracking
    font.capitalization: Font.AllUppercase
    elide: Text.ElideRight

    Behavior on color {
        ColorAnimation { duration: Motion.fast }
    }
}
