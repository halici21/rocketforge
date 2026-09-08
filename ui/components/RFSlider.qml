import QtQuick
import QtQuick.Controls
import "../theme"

/*
 * RFSlider - a continuous control drawn as an instrument scale rather than a
 * consumer volume slider: a hairline track, a filled span, evenly spaced ticks
 * and a square handle with a centre line to read the position against.
 */
Slider {
    id: control

    property int tickCount: 11
    property bool showTicks: true

    implicitHeight: 26
    implicitWidth: 240
    padding: 0

    background: Item {
        anchors.fill: parent

        // Ticks sit under the track and act as the scale.
        Row {
            visible: control.showTicks
            width: parent.width - handleSize
            x: handleSize / 2
            y: parent.height / 2 + 7
            spacing: (width - control.tickCount) / (control.tickCount - 1)

            readonly property real handleSize: 14

            Repeater {
                model: control.tickCount
                delegate: Rectangle {
                    required property int index
                    width: Metrics.hairline
                    height: index === 0 || index === control.tickCount - 1 ? 6 : 4
                    color: Theme.divider
                }
            }
        }

        Rectangle {
            id: track
            x: 7
            width: parent.width - 14
            height: 2
            radius: 1
            y: (parent.height - height) / 2 - 2
            color: Theme.surfaceSunken
            border.width: Metrics.hairline
            border.color: Theme.divider

            Rectangle {
                width: control.visualPosition * parent.width
                height: parent.height
                radius: 1
                color: Theme.accent
                opacity: control.enabled ? 0.85 : 0.35
            }
        }
    }

    handle: Rectangle {
        x: control.visualPosition * (control.availableWidth - width)
        y: (control.height - height) / 2 - 2
        implicitWidth: 14
        implicitHeight: 14
        radius: Metrics.radius.xs
        color: Theme.surfaceElevated
        border.width: control.pressed || control.hovered ? 1.5 : 1.2
        border.color: control.enabled ? Theme.accent : Theme.border

        Behavior on border.width { NumberAnimation { duration: Motion.fast } }

        // Centre line: the reading edge of the handle.
        Rectangle {
            anchors.centerIn: parent
            width: Metrics.hairline
            height: 6
            color: Theme.accent
            opacity: 0.9
        }

        Rectangle {
            anchors.fill: parent
            anchors.margins: -3
            radius: Metrics.radius.s
            color: "transparent"
            border.width: Metrics.focusRing
            border.color: Theme.accent
            visible: control.activeFocus
        }
    }
}
