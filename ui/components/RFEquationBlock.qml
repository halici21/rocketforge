import QtQuick
import "../theme"

/*
 * RFEquationBlock - a relation shown for reference.
 *
 * The text is static rich text (italic variables, real subscripts and
 * exponents). Nothing here is parsed and nothing is evaluated; this is the
 * surface that the equation/reference module will grow into.
 */
Rectangle {
    id: root

    property string equation: ""
    property string caption: ""

    implicitHeight: column.implicitHeight + Metrics.spacing.l * 2
    color: Theme.surfaceSubtle
    radius: Metrics.radius.l
    border.width: Metrics.hairline
    border.color: Theme.divider

    Behavior on color { ColorAnimation { duration: Motion.fast } }

    Column {
        id: column
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: Metrics.spacing.l
        anchors.rightMargin: Metrics.spacing.l
        spacing: Metrics.spacing.s

        Text {
            width: parent.width
            text: root.equation
            textFormat: Text.RichText
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            color: Theme.text
            font.family: Typography.sans
            font.pixelSize: Typography.body + 2
        }

        Text {
            width: parent.width
            visible: root.caption !== ""
            text: Notation.rich(root.caption)
            textFormat: Notation.textFormat(root.caption)
            horizontalAlignment: Text.AlignHCenter
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
    }
}
