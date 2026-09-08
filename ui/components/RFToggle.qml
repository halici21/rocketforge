import QtQuick
import QtQuick.Controls
import "../theme"

/*
 * A binary switch, sized to sit on the same line as body text.
 */
Switch {
    id: control

    implicitHeight: Metrics.touchTarget
    padding: 0
    spacing: Metrics.spacing.s

    indicator: Rectangle {
        implicitWidth: 34
        implicitHeight: 18
        x: 0
        y: (control.height - height) / 2
        radius: 9
        color: control.checked ? Theme.accent : Theme.surfaceSunken
        border.width: Metrics.hairline
        border.color: control.checked ? Theme.accent : Theme.border
        opacity: control.enabled ? 1 : 0.45

        Behavior on color { ColorAnimation { duration: Motion.base } }

        Rectangle {
            x: control.checked ? parent.width - width - 2 : 2
            y: 2
            width: 14
            height: 14
            radius: 7
            color: control.checked ? Theme.accentContrast : Theme.textSecondary

            Behavior on x { NumberAnimation { duration: Motion.base; easing.type: Motion.standard } }
            Behavior on color { ColorAnimation { duration: Motion.base } }
        }

        Rectangle {
            anchors.fill: parent
            anchors.margins: -3
            radius: 12
            color: "transparent"
            border.width: Metrics.focusRing
            border.color: Theme.accent
            visible: control.activeFocus
        }
    }

    contentItem: Text {
        text: control.text
        color: control.enabled ? Theme.text : Theme.textDisabled
        font.family: Typography.sans
        font.pixelSize: Typography.body
        verticalAlignment: Text.AlignVCenter
        leftPadding: control.indicator.width + control.spacing
    }
}
