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
    property string scale: "medium"    // large | medium | small
    property bool highlighted: false

    readonly property real valueSize: scale === "large" ? Typography.readoutLarge
                                    : scale === "small" ? Typography.readoutSmall
                                    : Typography.readoutMedium

    implicitWidth: Math.max(labelText.implicitWidth, valueRow.implicitWidth)
    implicitHeight: labelText.implicitHeight + Metrics.spacing.xs + valueRow.implicitHeight

    Text {
        id: labelText
        width: root.width
        text: root.label
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.meta
        font.weight: Typography.medium
        font.letterSpacing: 0.6
        elide: Text.ElideRight
    }

    RowLayout {
        id: valueRow
        anchors.top: labelText.bottom
        anchors.topMargin: Metrics.spacing.xs
        spacing: 4

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
