import QtQuick
import "../theme"

/*
 * The prose twin of RFNumberField: same label-and-rule anatomy, set in the
 * sans face because the content is a name, not a quantity.
 */
Item {
    id: root

    property string label: ""
    property string placeholder: ""
    property alias text: input.text
    property alias readOnly: input.readOnly

    signal edited()

    /* forceActiveFocus() on the wrapper would focus the wrapper, not the text.
     * Renaming from elsewhere in the application goes through here. */
    function focusInput() {
        input.forceActiveFocus()
        input.selectAll()
    }

    implicitWidth: 180
    implicitHeight: (labelText.visible ? labelText.implicitHeight + Metrics.spacing.xs : 0)
                    + Math.max(input.implicitHeight, Metrics.touchTarget)
                    + Metrics.spacing.xs + 2

    Text {
        id: labelText
        visible: root.label !== ""
        text: Notation.rich(root.label)
        textFormat: Notation.textFormat(root.label)
        color: root.enabled ? Theme.textSecondary : Theme.textDisabled
        font.family: Typography.sans
        font.pixelSize: Typography.inputLabel
        elide: Text.ElideRight
        clip: true              // RichText does not elide
        width: root.width
    }

    Item {
        id: valueRow
        anchors.top: labelText.visible ? labelText.bottom : parent.top
        anchors.topMargin: labelText.visible ? Metrics.spacing.xs : 0
        width: root.width
        height: Math.max(input.implicitHeight, Metrics.touchTarget)

        TextInput {
            id: input
            anchors.fill: parent
            verticalAlignment: TextInput.AlignVCenter
            color: root.enabled ? Theme.text : Theme.textDisabled
            font.family: Typography.sans
            font.pixelSize: Typography.body
            selectByMouse: true
            selectionColor: Theme.accent
            selectedTextColor: Theme.accentContrast
            activeFocusOnTab: true
            clip: true
            onEditingFinished: root.edited()
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: root.placeholder
            visible: input.text === "" && !input.activeFocus
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.body
        }
    }

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
        cursorShape: root.enabled && !input.readOnly ? Qt.IBeamCursor : Qt.ArrowCursor
    }
}
