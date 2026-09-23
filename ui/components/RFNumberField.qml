import QtQuick
import "../theme"

/*
 * RFNumberField - the primary engineering input.
 *
 * Label above, the number itself set large in the monospaced face, and a single
 * hairline rule that carries the focus state. No filled box, no floating label:
 * the value is the loudest thing in the control, which is how a workstation
 * form should read. Steppers appear on hover so the resting state stays clean.
 *
 * The control edits text. It does not validate against any physical range and
 * nothing downstream is computed from it in this phase.
 */
Item {
    id: root

    property string label: ""
    property string unit: ""
    property real step: 0.01
    property int decimals: 3
    property bool showSteppers: true
    property alias text: input.text
    property alias readOnly: input.readOnly

    signal edited()

    implicitWidth: 180
    implicitHeight: labelText.implicitHeight + Metrics.spacing.xs
                    + Math.max(input.implicitHeight, Metrics.touchTarget)
                    + Metrics.spacing.xs + 2

    readonly property bool interactive: enabled && !input.readOnly

    function nudge(direction) {
        var current = parseFloat(input.text)
        if (isNaN(current))
            current = 0
        input.text = (current + direction * root.step).toFixed(root.decimals)
        root.edited()
    }

    Text {
        id: labelText
        text: Notation.rich(root.label)
        textFormat: Notation.textFormat(root.label)
        color: root.enabled ? Theme.textSecondary : Theme.textDisabled
        font.family: Typography.sans
        font.pixelSize: Typography.inputLabel
        elide: Text.ElideRight
        // RichText does not elide; a label carrying notation is clipped
        // to its width instead of running into its neighbour.
        clip: true
        width: root.width
    }

    Item {
        id: valueRow
        anchors.top: labelText.bottom
        anchors.topMargin: Metrics.spacing.xs
        width: root.width
        height: Math.max(input.implicitHeight, Metrics.touchTarget)

        TextInput {
            id: input
            anchors.left: parent.left
            anchors.right: unitText.left
            anchors.rightMargin: Metrics.spacing.s
            anchors.verticalCenter: parent.verticalCenter
            text: "0.000"
            color: root.enabled ? Theme.text : Theme.textDisabled
            font.family: Typography.mono
            font.pixelSize: Typography.inputValue
            font.weight: Typography.medium
            selectByMouse: true
            selectionColor: Theme.accent
            selectedTextColor: Theme.accentContrast
            activeFocusOnTab: true
            clip: true
            // Engineering input is always written with a decimal point.
            validator: DoubleValidator { locale: "C" }

            onEditingFinished: root.edited()
            Keys.onUpPressed: root.nudge(1)
            Keys.onDownPressed: root.nudge(-1)
        }

        Text {
            id: unitText
            anchors.right: steppers.visible ? steppers.left : parent.right
            anchors.rightMargin: steppers.visible ? Metrics.spacing.s : 0
            anchors.verticalCenter: parent.verticalCenter
            text: root.unit
            visible: root.unit !== ""
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.bodySmall
        }

        Column {
            id: steppers
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            spacing: 1
            visible: root.showSteppers && root.interactive
            opacity: hover.hovered || input.activeFocus ? 1 : 0

            Behavior on opacity { NumberAnimation { duration: Motion.fast } }

            RFIconButton {
                icon: "caret-up"
                size: 15
                iconSize: 13
                onClicked: root.nudge(1)
            }
            RFIconButton {
                icon: "caret-down"
                size: 15
                iconSize: 13
                onClicked: root.nudge(-1)
            }
        }
    }

    // Focus rule.
    Rectangle {
        anchors.top: valueRow.bottom
        anchors.topMargin: Metrics.spacing.xs
        width: root.width
        height: input.activeFocus ? 1.5 : Metrics.hairline
        color: !root.enabled ? Theme.divider
             : input.activeFocus ? Theme.accent
             : hover.hovered ? Theme.borderStrong
             : Theme.border

        Behavior on color { ColorAnimation { duration: Motion.fast } }
        Behavior on height { NumberAnimation { duration: Motion.fast } }
    }

    HoverHandler {
        id: hover
        cursorShape: root.interactive ? Qt.IBeamCursor : Qt.ArrowCursor
    }
}
