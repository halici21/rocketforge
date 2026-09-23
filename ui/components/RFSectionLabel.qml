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
    // A label carrying notation arrives from Notation.sectionRich already
    // uppercased where it may be: uppercasing a symbol changes it (p -> P).
    font.capitalization: textFormat === Text.RichText ? Font.MixedCase
                                                      : Font.AllUppercase
    elide: Text.ElideRight
    clip: textFormat === Text.RichText          // RichText does not elide

    Behavior on color {
        ColorAnimation { duration: Motion.fast }
    }
}
