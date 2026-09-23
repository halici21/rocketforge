import QtQuick
import QtQuick.Layouts
import "../theme"

/*
 * One engineering quantity: a quiet label above, the number below in the
 * monospaced face so that columns of results line up digit for digit.
 * The unit sits on the number's baseline, one step down in weight.
 */
Item {
    id: root

    property string label: ""
    property string value: "-"
    property string unit: ""
    property string scale: "medium"    // hero | large | medium | small
    property bool highlighted: false

    // "hero" is the one number a workspace exists to produce
    // (rf-engineering-workbench hierarchy Level 1, Analysis Experience R2).
    readonly property real valueSize: scale === "hero" ? Typography.readoutHero
                                    : scale === "large" ? Typography.readoutLarge
                                    : scale === "small" ? Typography.readoutSmall
                                    : Typography.readoutMedium

    implicitWidth: Math.max(labelText.implicitWidth, valueRow.implicitWidth)
    implicitHeight: labelText.implicitHeight + Metrics.spacing.xs + valueRow.implicitHeight

    Text {
        id: labelText
        width: root.width
        text: Notation.rich(root.label)
        textFormat: Notation.textFormat(root.label)
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.meta
        font.weight: Typography.medium
        font.letterSpacing: 0.6
        elide: Text.ElideRight
        // RichText does not elide; a label carrying notation is clipped
        // to its width instead of running into its neighbour.
        clip: true
    }

    RowLayout {
        id: valueRow
        anchors.top: labelText.bottom
        anchors.topMargin: Metrics.spacing.xs
        spacing: 6

        Text {
            text: root.value
            color: root.highlighted ? Theme.accent : Theme.text
            font.family: Typography.mono
            font.pixelSize: root.valueSize
            font.weight: Typography.medium
            Layout.alignment: Qt.AlignBaseline

            Behavior on color { ColorAnimation { duration: Motion.base } }
        }

        Text {
            visible: root.unit !== ""
            text: root.unit
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.bodySmall
            Layout.alignment: Qt.AlignBaseline
        }
    }
}
