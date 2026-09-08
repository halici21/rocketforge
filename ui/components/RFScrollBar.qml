import QtQuick
import QtQuick.Controls
import "../theme"

/*
 * A scrollbar that stays out of the way: a thin bar with no track chrome,
 * fading in when the surface is scrolled or hovered.
 */
ScrollBar {
    id: control

    implicitWidth: 10
    padding: 2
    minimumSize: 0.08
    policy: ScrollBar.AsNeeded

    contentItem: Rectangle {
        implicitWidth: 4
        radius: 2
        color: control.pressed ? Theme.textMuted
             : control.hovered ? Theme.borderStrong
             : Theme.border
        opacity: control.policy === ScrollBar.AlwaysOn || control.active ? 1 : 0

        Behavior on opacity { NumberAnimation { duration: Motion.base } }
        Behavior on color { ColorAnimation { duration: Motion.fast } }
    }

    background: Item {}
}
